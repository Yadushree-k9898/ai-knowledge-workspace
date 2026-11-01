"""Document upload, status, listing, and deletion endpoints."""

import logging

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ResourceNotFound, ValidationError
from app.core.rate_limit import rate_limit
from app.db.models import Document, DocumentChunk
from app.db.models.project import Project
from app.db.models.project_document import ProjectDocument
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.audit.service import record_audit_event
from app.modules.documents import service as document_service
from app.modules.notifications.service import create_notification
from app.services.chunking_service import chunk_text
from app.services.document_parser import parse_document
from app.services.embedding_service import generate_embeddings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])
project_router = APIRouter(prefix="/api/v1/projects", tags=["Project Documents"])
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


async def _enqueue_document_job(job_id: int, attempt: int) -> bool:
    """Queue a committed job; its database record survives a Redis outage."""
    redis = None
    try:
        redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        result = await redis.enqueue_job(
            "process_document",
            job_id,
            _job_id=f"document-{job_id}-attempt-{attempt}",
        )
        return result is not None
    except Exception:
        logger.exception("Could not enqueue document job %s; it remains pending.", job_id)
        return False
    finally:
        if redis is not None:
            await redis.close()


@project_router.post(
    "/{project_id}/documents",
    status_code=202,
    dependencies=[Depends(rate_limit("document-upload", limit=20, window_seconds=3600))],
)
async def upload_project_document(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Accept an upload quickly and process it in the background."""
    file_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise ValidationError("Files must be 10 MB or smaller.")

    document, job = document_service.create_project_document_job(
        db,
        project_id=project_id,
        user_id=user["id"],
        filename=file.filename or "",
        file_bytes=file_bytes,
    )
    queued = await _enqueue_document_job(job.id, job.attempts + 1)
    return {
        "data": {
            "id": document.id,
            "job_id": job.id,
            "filename": document.filename,
            "status": job.status,
            "queued": queued,
            "created_at": document.created_at,
        }
    }


@project_router.get("/{project_id}/documents/{document_id}/status")
async def get_project_document_status(
    project_id: str,
    document_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Return processing state only to a user who can access the project."""
    document, job = document_service.get_project_document_job(
        db,
        project_id=project_id,
        document_id=document_id,
        user_id=user["id"],
    )
    return {"data": {
        "document_id": document.id,
        "job_id": job.id,
        "filename": document.filename,
        "status": job.status,
        "attempts": job.attempts,
        "error": job.error,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }}


@project_router.post("/{project_id}/documents/{document_id}/retry", status_code=202)
async def retry_project_document(
    project_id: str,
    document_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Requeue a failed or pending job without uploading the file again."""
    job = document_service.retry_project_document_job(
        db,
        project_id=project_id,
        document_id=document_id,
        user_id=user["id"],
    )
    queued = await _enqueue_document_job(job.id)
    return {"data": {"job_id": job.id, "status": job.status, "queued": queued}}


@project_router.get("/{project_id}/documents")
async def list_project_documents(
    project_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    documents = document_service.list_project_documents(
        db,
        project_id=project_id,
        user_id=user["id"],
    )
    return {"data": [{
        "id": document.id,
        "filename": document.filename,
        "created_at": document.created_at,
        "added_at": link.added_at,
        "status": job.status if job else "READY",
        "processing_error": job.error if job else None,
    } for document, link, job in documents]}


@project_router.delete("/{project_id}/documents/{document_id}")
async def remove_project_document(
    project_id: str,
    document_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    document_service.remove_document_from_project(
        db,
        project_id=project_id,
        document_id=document_id,
        user_id=user["id"],
    )
    return {"data": {"message": "Document removed from project."}}


@router.post(
    "/upload",
    dependencies=[Depends(rate_limit("document-upload", limit=20, window_seconds=3600))],
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Legacy personal upload endpoint; project uploads use the ARQ pipeline."""
    file_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise ValidationError("Files must be 10 MB or smaller.")
    if not file_bytes:
        raise ValidationError("Empty files cannot be uploaded.")
    try:
        text_content = parse_document(file.filename or "", file_bytes)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    chunks = chunk_text(text_content)
    if not chunks:
        raise ValidationError("No text could be extracted from this document.")
    embeddings = generate_embeddings(chunks)
    if len(embeddings) != len(chunks):
        raise RuntimeError("The embedding service returned an incomplete result.")

    document = Document(
        user_id=user["id"],
        filename=file.filename or "upload",
        content=text_content,
    )
    db.add(document)
    db.flush()
    db.add_all([
        DocumentChunk(
            document_id=document.id,
            text_content=chunk,
            embedding=embedding,
        )
        for chunk, embedding in zip(chunks, embeddings)
    ])
    create_notification(
        db,
        user_id=user["id"],
        notification_type="DOCUMENT_PROCESSED",
        title="Document processing completed",
        message=f"'{document.filename}' was uploaded and processed successfully.",
    )
    db.commit()
    return {
        "message": "Document uploaded and processed successfully",
        "document_id": document.id,
        "filename": document.filename,
        "chunks_created": len(chunks),
    }


@router.get("/")
async def list_documents(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    docs = db.query(Document).filter(
        Document.user_id == user["id"]
    ).order_by(Document.created_at.desc()).all()
    return [{
        "id": doc.id,
        "filename": doc.filename,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    } for doc in docs]


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user["id"],
    ).first()
    if not doc:
        raise ResourceNotFound("Document")

    linked_projects = (
        db.query(Project.organization_id, Project.id)
        .join(ProjectDocument, ProjectDocument.project_id == Project.id)
        .filter(ProjectDocument.document_id == doc.id)
        .all()
    )
    projects_by_organization = {}
    for organization_id, project_id in linked_projects:
        projects_by_organization.setdefault(organization_id, []).append(project_id)
    for organization_id, project_ids in projects_by_organization.items():
        record_audit_event(
            db,
            organization_id=organization_id,
            user_id=user["id"],
            action="DOCUMENT_DELETED",
            resource_type="document",
            resource_id=doc.id,
            metadata={"project_ids": project_ids},
        )

    db.delete(doc)
    db.commit()
    return {"message": f"Document '{doc.filename}' deleted successfully"}
