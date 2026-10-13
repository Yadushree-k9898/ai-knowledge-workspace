"""Database access for persisted research reports."""

from sqlalchemy.orm import Session

from app.db.models.research_report import ResearchReport


def create_report(
    db: Session,
    *,
    report_id: str,
    project_id: str,
    user_id: str,
    title: str,
    report_type: str,
    instructions: str | None,
    source_document_ids: list[int],
) -> ResearchReport:
    report = ResearchReport(
        id=report_id,
        project_id=project_id,
        created_by=user_id,
        title=title,
        report_type=report_type,
        instructions=instructions,
        source_document_ids=source_document_ids,
        status="QUEUED",
    )
    db.add(report)
    db.flush()
    return report


def get_report(db: Session, report_id: str) -> ResearchReport | None:
    return (
        db.query(ResearchReport)
        .filter(ResearchReport.id == report_id)
        .first()
    )


def list_project_reports(db: Session, project_id: str, limit: int = 50) -> list[ResearchReport]:
    return (
        db.query(ResearchReport)
        .filter(ResearchReport.project_id == project_id)
        .order_by(ResearchReport.created_at.desc())
        .limit(limit)
        .all()
    )


def delete_report(db: Session, report: ResearchReport) -> None:
    db.delete(report)
    db.flush()