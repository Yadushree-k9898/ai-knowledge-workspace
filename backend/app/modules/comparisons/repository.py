"""Database queries for project documents and persisted comparisons."""

from sqlalchemy.orm import Session

from app.db.models.comparison import ProjectComparison
from app.db.models.project_document import ProjectDocument


def list_project_document_links(db: Session, project_id: str) -> list[ProjectDocument]:
    return (
        db.query(ProjectDocument)
        .filter(ProjectDocument.project_id == project_id)
        .order_by(ProjectDocument.added_at.desc(), ProjectDocument.document_id.desc())
        .all()
    )


def get_project_document_link(
    db: Session, project_id: str, document_id: int
) -> ProjectDocument | None:
    return (
        db.query(ProjectDocument)
        .filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.document_id == document_id,
        )
        .first()
    )


def add_project_document(
    db: Session, *, project_id: str, document_id: int, user_id: str
) -> ProjectDocument:
    link = ProjectDocument(
        project_id=project_id,
        document_id=document_id,
        added_by=user_id,
    )
    db.add(link)
    db.flush()
    return link


def create_comparison(
    db: Session,
    *,
    comparison_id: str,
    project_id: str,
    user_id: str,
    document_ids: list[int],
    instructions: str | None,
) -> ProjectComparison:
    comparison = ProjectComparison(
        id=comparison_id,
        project_id=project_id,
        created_by=user_id,
        document_ids=document_ids,
        instructions=instructions,
        status="QUEUED",
    )
    db.add(comparison)
    db.flush()
    return comparison


def get_comparison(
    db: Session, *, project_id: str, comparison_id: str
) -> ProjectComparison | None:
    return (
        db.query(ProjectComparison)
        .filter(
            ProjectComparison.project_id == project_id,
            ProjectComparison.id == comparison_id,
        )
        .first()
    )


def list_comparisons(db: Session, project_id: str, limit: int = 20) -> list[ProjectComparison]:
    return (
        db.query(ProjectComparison)
        .filter(ProjectComparison.project_id == project_id)
        .order_by(ProjectComparison.created_at.desc())
        .limit(limit)
        .all()
    )