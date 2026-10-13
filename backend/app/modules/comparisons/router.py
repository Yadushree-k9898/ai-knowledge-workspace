"""Project document linking and asynchronous comparison endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.core.logging import get_logger
from app.db.models.project import Project
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.comparisons import service
from app.modules.comparisons.schemas import (
    AttachProjectDocumentRequest,
    ComparisonResponse,
    CreateComparisonRequest,
    ProjectDocumentResponse,
)
from app.modules.projects.dependencies import (
    get_project_with_access,
    get_project_with_write_access,
)
from app.workers.queue import create_queue_pool

logger = get_logger("comparisons.router")
router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["Comparisons"])


@router.get("/documents", summary="List documents linked to a project")
async def list_project_documents(
    project: Project = Depends(get_project_with_access),
    db: Session = Depends(get_db),
):
    documents = service.list_project_documents(db, project.id)
    return {"data": [ProjectDocumentResponse(**document) for document in documents]}


@router.post("/documents", summary="Add an owned document to a project")
async def add_project_document(
    body: AttachProjectDocumentRequest,
    project: Project = Depends(get_project_with_write_access),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = service.attach_document(
        db,
        project=project,
        document_id=body.document_id,
        user_id=user["id"],
    )
    return {"data": ProjectDocumentResponse(**document)}


@router.get("/comparisons", summary="List project comparisons")
async def list_project_comparisons(
    project: Project = Depends(get_project_with_access),
    db: Session = Depends(get_db),
):
    comparisons = service.list_comparisons(db, project.id)
    return {
        "data": [
            ComparisonResponse(**service.serialize_comparison(db, comparison))
            for comparison in comparisons
        ]
    }


@router.post(
    "/comparisons",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue a project document comparison",
    dependencies=[Depends(rate_limit("comparison-create", limit=10, window_seconds=3600))],
)
async def create_project_comparison(
    body: CreateComparisonRequest,
    project: Project = Depends(get_project_with_write_access),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comparison = service.create_comparison(
        db,
        project=project,
        user_id=user["id"],
        document_ids=body.document_ids,
        instructions=body.instructions,
    )

    queue = None
    try:
        queue = await create_queue_pool()
        await queue.enqueue_job("generate_comparison", comparison.id)
    except Exception as exc:
        service.mark_comparison_failed(db, comparison)
        logger.exception(
            "Could not queue document comparison.",
            extra={"user_id": user["id"], "resource_id": comparison.id},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The comparison worker is unavailable. Please try again later.",
        ) from exc
    finally:
        if queue is not None:
            try:
                await queue.close()
            except Exception:
                logger.warning(
                    "Could not close the Redis connection after enqueueing.",
                    extra={"resource_id": comparison.id},
                    exc_info=True,
                )

    db.refresh(comparison)
    return {
        "data": ComparisonResponse(
            **service.serialize_comparison(db, comparison)
        )
    }


@router.get("/comparisons/{comparison_id}", summary="Get comparison status and result")
async def get_project_comparison(
    comparison_id: str,
    project: Project = Depends(get_project_with_access),
    db: Session = Depends(get_db),
):
    comparison = service.get_comparison(
        db,
        project_id=project.id,
        comparison_id=comparison_id,
    )
    return {
        "data": ComparisonResponse(
            **service.serialize_comparison(db, comparison)
        )
    }