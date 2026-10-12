"""
Projects dependencies — FastAPI dependency injection.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.exceptions import ResourceNotFound, PermissionDenied
from app.db.models.project import Project
from app.modules.auth.dependencies import get_current_user
from app.modules.organizations import repository as org_repo
from app.modules.projects import repository as repo


def get_project_with_access(
    project_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    """
    FastAPI dependency that loads a project and verifies the current
    user is a member of the project's organization.
    """
    project = repo.get_project_by_id(db, project_id)
    if project is None:
        raise ResourceNotFound("Project")

    member = org_repo.get_member(db, project.organization_id, user["id"])
    if member is None:
        raise PermissionDenied("You are not a member of this organization.")

    return project
