"""Aggregate organization analytics from persisted product activity."""

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDenied, ValidationError
from app.db.models import Document, Project
from app.db.models.comparison import ProjectComparison
from app.db.models.project_document import ProjectDocument
from app.db.models.research_report import ResearchReport
from app.modules.organizations import repository as organization_repository

UNAVAILABLE_METRICS = [
    "documents_processed",
    "questions_asked",
    "processing_failures",
    "searches",
    "average_response_latency_ms",
    "ai_usage",
]


def get_organization_analytics(
    db: Session,
    *,
    organization_id: str,
    user_id: str,
    date_from: date,
    date_to: date,
) -> dict:
    if date_from > date_to:
        raise ValidationError("date_from must be on or before date_to.")

    if organization_repository.get_member(db, organization_id, user_id) is None:
        raise PermissionDenied("You are not a member of this organization.")

    start = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
    end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)

    documents_uploaded = (
        db.query(func.count(func.distinct(Document.id)))
        .join(ProjectDocument, ProjectDocument.document_id == Document.id)
        .join(Project, Project.id == ProjectDocument.project_id)
        .filter(
            Project.organization_id == organization_id,
            Document.created_at >= start,
            Document.created_at < end,
        )
        .scalar()
        or 0
    )

    reports_generated = (
        db.query(func.count(ResearchReport.id))
        .join(Project, Project.id == ResearchReport.project_id)
        .filter(
            Project.organization_id == organization_id,
            ResearchReport.status == "READY",
            ResearchReport.updated_at >= start,
            ResearchReport.updated_at < end,
        )
        .scalar()
        or 0
    )

    active_users: set[str] = set()
    active_users.update(
        user_id
        for (user_id,) in (
            db.query(Document.user_id)
            .join(ProjectDocument, ProjectDocument.document_id == Document.id)
            .join(Project, Project.id == ProjectDocument.project_id)
            .filter(
                Project.organization_id == organization_id,
                Document.created_at >= start,
                Document.created_at < end,
            )
            .distinct()
            .all()
        )
    )
    active_users.update(
        user_id
        for (user_id,) in (
            db.query(ResearchReport.created_by)
            .join(Project, Project.id == ResearchReport.project_id)
            .filter(
                Project.organization_id == organization_id,
                ResearchReport.created_at >= start,
                ResearchReport.created_at < end,
            )
            .distinct()
            .all()
        )
    )
    active_users.update(
        user_id
        for (user_id,) in (
            db.query(ProjectComparison.created_by)
            .join(Project, Project.id == ProjectComparison.project_id)
            .filter(
                Project.organization_id == organization_id,
                ProjectComparison.created_at >= start,
                ProjectComparison.created_at < end,
            )
            .distinct()
            .all()
        )
    )

    return {
        "organization_id": organization_id,
        "date_from": date_from,
        "date_to": date_to,
        "documents_uploaded": documents_uploaded,
        "documents_processed": None,
        "questions_asked": None,
        "reports_generated": reports_generated,
        "active_users": len(active_users),
        "processing_failures": None,
        "searches": None,
        "average_response_latency_ms": None,
        "ai_usage": None,
        "unavailable_metrics": UNAVAILABLE_METRICS.copy(),
    }