"""Business logic for project research report lifecycle."""

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDenied, ResourceNotFound, ValidationError
from app.db.models import Document
from app.db.models.organization_member import OrgRole
from app.db.models.project_document import ProjectDocument
from app.db.models.research_report import ResearchReport
from app.db.models.project import Project
from app.modules.audit.service import record_audit_event
from app.modules.organizations import repository as organization_repository
from app.modules.reports import repository as repo
from app.modules.reports.schemas import ReportType

MAX_REPORT_SOURCE_CHARACTERS = 200_000


def create_report(
    db: Session,
    *,
    project_id: str,
    user_id: str,
    title: str,
    report_type: ReportType,
    instructions: str | None,
) -> ResearchReport:
    documents = (
        db.query(Document)
        .join(ProjectDocument, ProjectDocument.document_id == Document.id)
        .filter(ProjectDocument.project_id == project_id)
        .order_by(ProjectDocument.added_at.asc())
        .all()
    )
    if not documents:
        raise ValidationError("Add at least one document to this project before generating a report.")

    total_characters = sum(len(document.content) for document in documents)
    if total_characters > MAX_REPORT_SOURCE_CHARACTERS:
        raise ValidationError(
            "The project's documents are too large for one report. Remove some documents and try again."
        )

    report = repo.create_report(
        db,
        report_id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=user_id,
        title=title,
        report_type=report_type.value,
        instructions=instructions,
        source_document_ids=[document.id for document in documents],
    )
    project = db.query(Project).filter(Project.id == project_id).one()
    record_audit_event(
        db,
        organization_id=project.organization_id,
        user_id=user_id,
        action="REPORT_CREATED",
        resource_type="report",
        resource_id=report.id,
        metadata={"project_id": project_id, "report_type": report_type.value},
    )
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, report_id: str) -> ResearchReport:
    report = repo.get_report(db, report_id)
    if report is None:
        raise ResourceNotFound("Report")
    return report


def get_project_report_access(
    db: Session,
    project_id: str,
    user_id: str,
    *,
    require_write: bool = False,
) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise ResourceNotFound("Project")
    member = organization_repository.get_member(db, project.organization_id, user_id)
    if member is None:
        raise PermissionDenied("You are not a member of this project's organization.")
    if require_write and member.role == OrgRole.VIEWER:
        raise PermissionDenied("Viewers cannot modify project reports.")
    return project


def list_project_reports(db: Session, project_id: str) -> list[ResearchReport]:
    return repo.list_project_reports(db, project_id)


def regenerate_report(db: Session, report: ResearchReport) -> ResearchReport:
    if report.status in {"QUEUED", "GENERATING"}:
        raise ValidationError("This report is already being generated.")
    report.status = "QUEUED"
    report.content = None
    report.error = None
    db.commit()
    db.refresh(report)
    return report


def mark_report_failed(
    db: Session, report: ResearchReport, message: str = "The report could not be queued. Please try again."
) -> None:
    report.status = "FAILED"
    report.error = message
    db.commit()


def delete_report(db: Session, report: ResearchReport, user_id: str) -> None:
    if report.created_by != user_id:
        raise PermissionDenied("Only the report creator can delete this report.")
    project = db.query(Project).filter(Project.id == report.project_id).one()
    record_audit_event(
        db,
        organization_id=project.organization_id,
        user_id=user_id,
        action="REPORT_DELETED",
        resource_type="report",
        resource_id=report.id,
        metadata={"project_id": project.id},
    )
    repo.delete_report(db, report)
    db.commit()