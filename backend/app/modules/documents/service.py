"""Project-scoped document upload, processing, listing, and unlink operations."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFound, ValidationError
from app.db.models import Document, DocumentChunk
from app.db.models.document_job import DocumentJob
from app.db.models.project_document import ProjectDocument
from app.db.session import SessionLocal
from app.modules.audit.service import record_audit_event
from app.modules.projects import service as project_service
from app.services.chunking_service import chunk_text
from app.services.document_parser import parse_document
from app.services.embedding_service import generate_embeddings


MAX_UPLOAD_BYTES = 10 * 1024 * 1024



def upload_project_document(
    db: Session,
    *,
    project_id: str,
    user_id: str,
    filename: str,
    file_bytes: bytes,
) -> tuple[Document, int]:
    """Synchronous compatibility path retained for existing callers and tests."""
    project = project_service.require_project_write_access(db, project_id, user_id)
    safe_filename = filename.replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not safe_filename:
        raise ValidationError("A file name is required.")
    if not file_bytes:
        raise ValidationError("Empty files cannot be uploaded.")
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise ValidationError("Files must be 10 MB or smaller.")
    try:
        content = parse_document(safe_filename, file_bytes)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if not content.strip():
        raise ValidationError("No text could be extracted from this document.")
    chunks = chunk_text(content)
    if not chunks:
        raise ValidationError("No text could be extracted from this document.")
    embeddings = generate_embeddings(chunks)
    if len(embeddings) != len(chunks):
        raise RuntimeError("The embedding service returned an incomplete result.")

    document = Document(user_id=user_id, filename=safe_filename, content=content)
    db.add(document)
    db.flush()
    db.add_all([
        DocumentChunk(document_id=document.id, text_content=chunk, embedding=embedding)
        for chunk, embedding in zip(chunks, embeddings)
    ])
    db.add(ProjectDocument(
        project_id=project.id, document_id=document.id, added_by=user_id
    ))
    record_audit_event(
        db,
        organization_id=project.organization_id,
        user_id=user_id,
        action="DOCUMENT_ADDED_TO_PROJECT",
        resource_type="document",
        resource_id=str(document.id),
        metadata={"project_id": project.id},
    )
    db.commit()
    db.refresh(document)
    return document, len(chunks)


def create_project_document_job(
    db: Session,
    *,
    project_id: str,
    user_id: str,
    filename: str,
    file_bytes: bytes,
) -> tuple[Document, DocumentJob]:
    """Commit the upload and durable job before attempting to enqueue Redis work."""
    project = project_service.require_project_write_access(db, project_id, user_id)
    safe_filename = filename.replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not safe_filename:
        raise ValidationError("A file name is required.")
    if not file_bytes:
        raise ValidationError("Empty files cannot be uploaded.")
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise ValidationError("Files must be 10 MB or smaller.")

    document = Document(user_id=user_id, filename=safe_filename, content="")
    db.add(document)
    db.flush()

    db.add(ProjectDocument(
        project_id=project.id,
        document_id=document.id,
        added_by=user_id,
    ))
    job = DocumentJob(
        document_id=document.id,
        project_id=project.id,
        requested_by=user_id,
        file_data=file_bytes,
        status="PENDING",
    )
    db.add(job)
    record_audit_event(
        db,
        organization_id=project.organization_id,
        user_id=user_id,
        action="DOCUMENT_ADDED_TO_PROJECT",
        resource_type="document",
        resource_id=str(document.id),
        metadata={"project_id": project.id, "processing_status": "PENDING"},
    )
    db.commit()
    db.refresh(document)
    db.refresh(job)
    return document, job


def process_document_job(job_id: int) -> None:
    """Extract, chunk, embed, and persist one document from a durable job."""
    db = SessionLocal()
    try:
        job = db.query(DocumentJob).filter(DocumentJob.id == job_id).with_for_update().first()
        if job is None or job.status == "COMPLETED":
            return
        if job.status == "PROCESSING":
            # A second enqueue must not process the same document concurrently.
            return

        document = db.query(Document).filter(Document.id == job.document_id).first()
        if document is None:
            job.status = "FAILED"
            job.error = "The uploaded document no longer exists."
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
            return

        job.status = "PROCESSING"
        job.attempts += 1
        job.started_at = datetime.now(timezone.utc)
        job.error = None
        db.commit()

        content = parse_document(document.filename, job.file_data)
        if not content.strip():
            raise ValueError("No text could be extracted from this document.")

        chunks = chunk_text(content)
        if not chunks:
            raise ValueError("No text could be extracted from this document.")

        embeddings = generate_embeddings(chunks)
        if len(embeddings) != len(chunks):
            raise RuntimeError("The embedding service returned an incomplete result.")

        document.content = content
        db.add_all([
            DocumentChunk(
                document_id=document.id,
                text_content=chunk,
                embedding=embedding,
            )
            for chunk, embedding in zip(chunks, embeddings)
        ])
        job.file_data = b""
        job.status = "COMPLETED"
        job.error = None
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()
        failed_job = db.query(DocumentJob).filter(DocumentJob.id == job_id).first()
        if failed_job is not None:
            failed_job.status = "FAILED"
            failed_job.error = "Document processing failed. Please retry the job."
            failed_job.finished_at = datetime.now(timezone.utc)
            db.commit()
        raise
    finally:
        db.close()


def get_project_document_job(
    db: Session, *, project_id: str, document_id: int, user_id: str
) -> tuple[Document, DocumentJob]:
    project_service.get_project(db, project_id, user_id)
    row = (
        db.query(Document, DocumentJob)
        .join(DocumentJob, DocumentJob.document_id == Document.id)
        .filter(Document.id == document_id, DocumentJob.project_id == project_id)
        .first()
    )
    if row is None:
        raise ResourceNotFound("Document job")
    return row


def retry_project_document_job(
    db: Session, *, project_id: str, document_id: int, user_id: str
) -> DocumentJob:
    project_service.require_project_write_access(db, project_id, user_id)
    job = (
        db.query(DocumentJob)
        .filter(
            DocumentJob.document_id == document_id,
            DocumentJob.project_id == project_id,
        )
        .first()
    )
    if job is None:
        raise ResourceNotFound("Document job")
    stale_processing = (
        job.status == "PROCESSING"
        and job.started_at is not None
        and job.started_at < datetime.now(timezone.utc) - timedelta(minutes=15)
    )
    if job.status not in {"FAILED", "PENDING"} and not stale_processing:
        raise ValidationError("Only pending, failed, or stale processing jobs can be retried.")
    job.status = "PENDING"
    job.error = None
    job.finished_at = None
    db.commit()
    db.refresh(job)
    return job


def list_project_documents(
    db: Session, *, project_id: str, user_id: str
) -> list[tuple[Document, ProjectDocument]]:
    project_service.get_project(db, project_id, user_id)
    return (
        db.query(Document, ProjectDocument)
        .join(ProjectDocument, ProjectDocument.document_id == Document.id)
        .filter(ProjectDocument.project_id == project_id)
        .order_by(ProjectDocument.added_at.desc(), Document.id.desc())
        .all()
    )


def remove_document_from_project(
    db: Session, *, project_id: str, document_id: int, user_id: str
) -> None:
    project = project_service.require_project_write_access(db, project_id, user_id)
    link = (
        db.query(ProjectDocument)
        .filter(
            ProjectDocument.project_id == project.id,
            ProjectDocument.document_id == document_id,
        )
        .first()
    )
    if link is None:
        raise ResourceNotFound("Project document")

    record_audit_event(
        db,
        organization_id=project.organization_id,
        user_id=user_id,
        action="DOCUMENT_REMOVED_FROM_PROJECT",
        resource_type="document",
        resource_id=str(document_id),
        metadata={"project_id": project.id},
    )
    db.delete(link)
    db.commit()
