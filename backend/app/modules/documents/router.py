from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.db.models import Document, DocumentChunk
from app.db.models.project import Project
from app.db.models.project_document import ProjectDocument
from app.modules.auth.dependencies import get_current_user
from app.modules.audit.service import record_audit_event
from app.services.document_parser import parse_document
from app.services.chunking_service import chunk_text
from app.services.embedding_service import generate_embeddings
from app.modules.notifications.service import create_notification

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])

@router.post(
    "/upload",
    dependencies=[Depends(rate_limit("document-upload", limit=20, window_seconds=3600))],
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Upload a document, extract text, chunk it, and generate embeddings."""
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        text_content = parse_document(file.filename, file_bytes)
    except ValueError as e:
        create_notification(
            db,
            user_id=user["id"],
            notification_type="DOCUMENT_PROCESSING_FAILED",
            title="Document processing failed",
            message=f"'{file.filename}' could not be processed: {e}",
        )
        db.commit()
        raise HTTPException(status_code=400, detail=str(e))

    if not text_content.strip():
        create_notification(
            db,
            user_id=user["id"],
            notification_type="DOCUMENT_PROCESSING_FAILED",
            title="Document processing failed",
            message=f"No text could be extracted from '{file.filename}'.",
        )
        db.commit()
        raise HTTPException(status_code=400, detail="No text could be extracted from this document")

    # Save document to DB
    doc = Document(
        user_id=user["id"],
        filename=file.filename,
        content=text_content,
    )
    db.add(doc)
    db.flush()

    # Chunk the text
    chunks = chunk_text(text_content)

    # Generate embeddings for all chunks
    embeddings = generate_embeddings(chunks)

    # Save chunks with embeddings to DB
    for chunk_text_content, embedding in zip(chunks, embeddings):
        chunk = DocumentChunk(
            document_id=doc.id,
            text_content=chunk_text_content,
            embedding=embedding,
        )
        db.add(chunk)

    create_notification(
        db,
        user_id=user["id"],
        notification_type="DOCUMENT_PROCESSED",
        title="Document processing completed",
        message=f"'{doc.filename}' was uploaded and processed successfully.",
    )
    db.commit()

    return {
        "message": "Document uploaded and processed successfully",
        "document_id": doc.id,
        "filename": file.filename,
        "chunks_created": len(chunks),
    }

@router.get("/")
async def list_documents(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List all documents uploaded by the current user."""
    docs = db.query(Document).filter(Document.user_id == user["id"]).order_by(Document.created_at.desc()).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        }
        for doc in docs
    ]

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Delete a document and all its chunks."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user["id"],
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

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
