"""Project-scoped document upload, listing, and unlink operations."""

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFound, ValidationError
from app.db.models import Document, DocumentChunk
from app.db.models.project_document import ProjectDocument
from app.modules.audit.service import record_audit_event
from app.modules.projects import service as project_service
from app.services.chunking_service import chunk_text
from app.services.document_parser import parse_document
from app.services.embedding_service import generate_embeddings


def upload_project_document(
    db: Session,
    *,
    project_id: str,
    user_id: str,
    filename: str,
    file_bytes: bytes,
) -> tuple[Document, int]:
    """Parse, embed, and attach a newly uploaded document in one transaction."""
    project = project_service.require_project_write_access(db, project_id, user_id)
    safe_filename = filename.replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not safe_filename:
        raise ValidationError("A file name is required.")
    if not file_bytes:
        raise ValidationError("Empty files cannot be uploaded.")

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
    db.add_all(
        [
            DocumentChunk(
                document_id=document.id,
                text_content=chunk,
                embedding=embedding,
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
    )
    db.add(
        ProjectDocument(
            project_id=project.id,
            document_id=document.id,
            added_by=user_id,
        )
    )
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


def list_project_documents(
    db: Session,
    *,
    project_id: str,
    user_id: str,
) -> list[tuple[Document, ProjectDocument]]:
    """List documents linked to a project after checking organization membership."""
    project_service.get_project(db, project_id, user_id)
    return (
        db.query(Document, ProjectDocument)
        .join(ProjectDocument, ProjectDocument.document_id == Document.id)
        .filter(ProjectDocument.project_id == project_id)
        .order_by(ProjectDocument.added_at.desc(), Document.id.desc())
        .all()
    )


def remove_document_from_project(
    db: Session,
    *,
    project_id: str,
    document_id: int,
    user_id: str,
) -> None:
    """Unlink a document from a project without deleting its file or chunks."""
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