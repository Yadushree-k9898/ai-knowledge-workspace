"""API endpoints for project research reports."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.rate_limit import rate_limit
from app.db.models.project import Project
from app.db.models.research_report import ResearchReport
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.audit.service import record_audit_event
from app.modules.projects.dependencies import get_project_with_access, get_project_with_write_access
from app.modules.reports import service
from app.modules.reports.schemas import CreateReportRequest, ReportResponse
from app.workers.queue import create_queue_pool

logger = get_logger("reports.router")
router = APIRouter(prefix="/api/v1", tags=["Research Reports"])


async def _enqueue_report(report: ResearchReport, db: Session) -> None:
    queue = None
    try:
        queue = await create_queue_pool()
        await queue.enqueue_job("generate_report", report.id)
    except Exception as exc:
        service.mark_report_failed(db, report)
        logger.exception("Could not queue research report.", extra={"resource_id": report.id})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The report worker is unavailable. Please try again later.",
        ) from exc
    finally:
        if queue is not None:
            try:
                await queue.close()
            except Exception:
                logger.warning(
                    "Could not close the Redis connection after enqueueing a report.",
                    extra={"resource_id": report.id},
                    exc_info=True,
                )
    db.refresh(report)


@router.get("/projects/{project_id}/reports", summary="List project research reports")
async def list_project_reports(
    project: Project = Depends(get_project_with_access),
    db: Session = Depends(get_db),
):
    reports = service.list_project_reports(db, project.id)
    return {"data": [ReportResponse.model_validate(report) for report in reports]}


@router.post(
    "/projects/{project_id}/reports",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue a research report",
    dependencies=[Depends(rate_limit("report-create", limit=10, window_seconds=3600))],
)
async def create_project_report(
    body: CreateReportRequest,
    project: Project = Depends(get_project_with_write_access),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = service.create_report(
        db,
        project_id=project.id,
        user_id=user["id"],
        title=body.title,
        report_type=body.report_type,
        instructions=body.instructions,
    )
    await _enqueue_report(report, db)
    return {"data": ReportResponse.model_validate(report)}


def _get_authorized_report(
    report_id: str,
    user_id: str,
    db: Session,
    *,
    require_write: bool = False,
) -> ResearchReport:
    report = service.get_report(db, report_id)
    service.get_project_report_access(
        db,
        report.project_id,
        user_id,
        require_write=require_write,
    )
    return report


@router.get("/reports/{report_id}", summary="Get report status and content")
async def get_report(
    report_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _get_authorized_report(report_id, user["id"], db)
    return {"data": ReportResponse.model_validate(report)}


@router.post(
    "/reports/{report_id}/regenerate",
    summary="Regenerate a report",
    dependencies=[Depends(rate_limit("report-regenerate", limit=10, window_seconds=3600))],
)
async def regenerate_report(
    report_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _get_authorized_report(report_id, user["id"], db, require_write=True)
    record_audit_event(
        db,
        organization_id=report.project.organization_id,
        user_id=user["id"],
        action="REPORT_REGENERATION_REQUESTED",
        resource_type="report",
        resource_id=report.id,
        metadata={"project_id": report.project_id},
    )
    report = service.regenerate_report(db, report)
    await _enqueue_report(report, db)
    return {"data": ReportResponse.model_validate(report)}


@router.delete(
    "/reports/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a report",
)
async def delete_report(
    report_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _get_authorized_report(report_id, user["id"], db)
    service.delete_report(db, report, user["id"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)