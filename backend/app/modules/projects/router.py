"""
Projects router — API endpoints for project management.

Endpoints:
    POST   /api/v1/organizations/{organization_id}/projects           — Create project
    GET    /api/v1/organizations/{organization_id}/projects           — List projects
    GET    /api/v1/projects/{project_id}                              — Get project
    PATCH  /api/v1/projects/{project_id}                              — Update project
    DELETE /api/v1/projects/{project_id}                              — Delete project
    GET    /api/v1/projects/{project_id}/summary                      — Get project summary
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.projects import service as project_service
from app.modules.projects.schemas import (
    CreateProjectRequest,
    UpdateProjectRequest,
    ProjectResponse,
    ProjectSummaryResponse,
    PaginationMeta,
)

router = APIRouter(prefix="/api/v1", tags=["Projects"])


# ---------------------------------------------------------------------------
# Organization-scoped endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/organizations/{organization_id}/projects",
    status_code=201,
    summary="Create project",
    dependencies=[Depends(rate_limit("project-create", limit=20, window_seconds=3600))],
)
async def create_project(
    organization_id: str,
    body: CreateProjectRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new project inside the organization.
    Requires at least MEMBER role (viewers cannot create).
    """
    project = project_service.create_project(
        db,
        org_id=organization_id,
        user_id=user["id"],
        name=body.name,
        description=body.description,
    )
    return {"data": ProjectResponse.model_validate(project)}


@router.get(
    "/organizations/{organization_id}/projects",
    summary="List projects",
)
async def list_projects(
    organization_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by name or description"),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List projects in the organization with pagination and optional search.
    """
    projects, total = project_service.list_projects(
        db,
        org_id=organization_id,
        user_id=user["id"],
        page=page,
        page_size=page_size,
        search=search,
    )
    return {
        "data": [ProjectResponse.model_validate(p) for p in projects],
        "pagination": PaginationMeta(page=page, page_size=page_size, total=total),
    }


# ---------------------------------------------------------------------------
# Project-scoped endpoints
# ---------------------------------------------------------------------------

@router.get("/projects/{project_id}", summary="Get project")
async def get_project(
    project_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get project details. Caller must be a member of the project's organization."""
    project = project_service.get_project(db, project_id, user["id"])
    return {"data": ProjectResponse.model_validate(project)}


@router.patch("/projects/{project_id}", summary="Update project")
async def update_project(
    project_id: str,
    body: UpdateProjectRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update project details. Requires at least MEMBER role."""
    project = project_service.update_project(
        db,
        project_id=project_id,
        user_id=user["id"],
        name=body.name,
        description=body.description,
    )
    return {"data": ProjectResponse.model_validate(project)}


@router.delete("/projects/{project_id}", status_code=200, summary="Delete project")
async def delete_project(
    project_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a project. Requires OWNER or ADMIN role."""
    project_service.delete_project(db, project_id=project_id, user_id=user["id"])
    return {"data": {"message": "Project has been deleted successfully."}}


@router.get("/projects/{project_id}/summary", summary="Get project summary")
async def get_project_summary(
    project_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get project summary with document, conversation, and report counts.
    """
    summary = project_service.get_project_summary(db, project_id=project_id, user_id=user["id"])
    return {"data": ProjectSummaryResponse(**summary)}
