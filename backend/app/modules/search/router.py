from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.search.schemas import ProjectSearchRequest, ProjectSearchResponse
from app.modules.search.service import search_project_documents

router = APIRouter(prefix="/api/v1/projects", tags=["Project Search"])


@router.post(
    "/{project_id}/search",
    response_model=ProjectSearchResponse,
    dependencies=[Depends(rate_limit("project-search", limit=60, window_seconds=60))],
)
async def search_project(
    project_id: str,
    request: ProjectSearchRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    results = search_project_documents(
        db,
        project_id=project_id,
        user_id=user["id"],
        query=request.query,
        limit=request.limit,
    )
    return {"data": results}