"""Business logic for project-scoped document comparisons."""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFound, ValidationError
from app.db.models import Document
from app.db.models.comparison import ProjectComparison
from app.db.models.project import Project
from app.db.models.project_document import ProjectDocument
from app.modules.comparisons import repository as repo
from app.modules.audit.service import record_audit_event

MAX_COMPARISON_CONTENT_CHARACTERS = 200_000


def _comparison_document_names(db: Session, comparison: ProjectComparison) -> list[str]:
    documents = (
        db.query(Document.id, Document.filename)
        .join(ProjectDocument, ProjectDocument.document_id == Document.id)
        .filter(
            ProjectDocument.project_id == comparison.project_id,
            Document.id.in_(comparison.document_ids),
        )
        .all()
    )
    names_by_id = {document_id: filename for document_id, filename in documents}
    return [
        names_by_id.get(document_id, "Document unavailable")
        for document_id in comparison.document_ids
    ]


def serialize_comparison(db: Session, comparison: ProjectComparison) -> dict:
    return {
        "id": comparison.id,
        "project_id": comparison.project_id,
        "document_ids": comparison.document_ids,
        "document_names": _comparison_document_names(db, comparison),
        "instructions": comparison.instructions,
        "status": comparison.status,
        "result": comparison.result,
        "error": comparison.error,
        "created_at": comparison.created_at,
        "updated_at": comparison.updated_at,
    }


def list_project_documents(db: Session, project_id: str) -> list[dict]:
    links = repo.list_project_document_links(db, project_id)
    documents = (
        db.query(Document)
        .filter(Document.id.in_([link.document_id for link in links]))
        .all()
    ) if links else []
    documents_by_id = {document.id: document for document in documents}
    return [
        {
            "id": link.document_id,
            "filename": documents_by_id[link.document_id].filename,
            "created_at": documents_by_id[link.document_id].created_at,
            "added_at": link.added_at,
        }
        for link in links
        if link.document_id in documents_by_id
    ]


def attach_document(
    db: Session, *, project: Project, document_id: int, user_id: str
) -> dict:
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == user_id)
        .first()
    )
    if document is None:
        raise ResourceNotFound("Document")

    link = repo.get_project_document_link(db, project.id, document_id)
    if link is None:
        try:
            link = repo.add_project_document(
                db,
                project_id=project.id,
                document_id=document_id,
                user_id=user_id,
            )
            record_audit_event(
                db,
                organization_id=project.organization_id,
                user_id=user_id,
                action="DOCUMENT_LINKED_TO_PROJECT",
                resource_type="document",
                resource_id=document_id,
                metadata={"project_id": project.id},
            )
            db.commit()
        except IntegrityError:
            db.rollback()
            link = repo.get_project_document_link(db, project.id, document_id)
            if link is None:
                raise
        db.refresh(link)

    return {
        "id": document.id,
        "filename": document.filename,
        "created_at": document.created_at,
        "added_at": link.added_at,
    }


def create_comparison(
    db: Session,
    *,
    project: Project,
    user_id: str,
    document_ids: list[int],
    instructions: str | None,
) -> ProjectComparison:
    linked_documents = (
        db.query(Document)
        .join(ProjectDocument, ProjectDocument.document_id == Document.id)
        .filter(
            ProjectDocument.project_id == project.id,
            Document.id.in_(document_ids),
        )
        .all()
    )
    if len(linked_documents) != len(document_ids):
        raise ValidationError("Choose 2 to 5 documents that are already in this project.")

    total_characters = sum(len(document.content) for document in linked_documents)
    if total_characters > MAX_COMPARISON_CONTENT_CHARACTERS:
        raise ValidationError(
            "The selected documents are too large to compare together. Choose shorter documents."
        )

    comparison = repo.create_comparison(
        db,
        comparison_id=str(uuid.uuid4()),
        project_id=project.id,
        user_id=user_id,
        document_ids=document_ids,
        instructions=instructions,
    )
    record_audit_event(
        db,
        organization_id=project.organization_id,
        user_id=user_id,
        action="COMPARISON_CREATED",
        resource_type="comparison",
        resource_id=comparison.id,
        metadata={"project_id": project.id, "document_count": len(document_ids)},
    )
    db.commit()
    db.refresh(comparison)
    return comparison


def get_comparison(
    db: Session, *, project_id: str, comparison_id: str
) -> ProjectComparison:
    comparison = repo.get_comparison(
        db,
        project_id=project_id,
        comparison_id=comparison_id,
    )
    if comparison is None:
        raise ResourceNotFound("Comparison")
    return comparison


def list_comparisons(db: Session, project_id: str) -> list[ProjectComparison]:
    return repo.list_comparisons(db, project_id)


def mark_comparison_failed(db: Session, comparison: ProjectComparison) -> None:
    comparison.status = "FAILED"
    comparison.error = "The comparison could not be queued. Please try again."
    db.commit()