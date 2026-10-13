"""
Projects service — business logic for project management.

Enforces org membership checks and delegates to the repository.
"""

import uuid

from sqlalchemy.orm import Session

from app.core.logging import log_security_event, get_logger
from app.core.exceptions import ResourceNotFound, PermissionDenied
from app.db.models.project import Project
from app.db.models.conversation import Conversation
from app.db.models.organization_member import OrgRole
from app.db.models.project_document import ProjectDocument
from app.db.models.research_report import ResearchReport
from app.modules.audit.service import record_audit_event
from app.modules.organizations import repository as org_repo
from app.modules.projects import repository as repo

logger = get_logger("projects.service")


def _require_membership(db: Session, org_id: str, user_id: str):
    """Verify user belongs to the organization."""
    member = org_repo.get_member(db, org_id, user_id)
    if member is None:
        raise PermissionDenied("You are not a member of this organization.")
    return member


def _require_write_access(db: Session, org_id: str, user_id: str):
    """Verify user has at least MEMBER role (can create/edit). Viewers cannot."""
    member = _require_membership(db, org_id, user_id)
    if member.role == OrgRole.VIEWER:
        raise PermissionDenied("Viewers cannot modify projects.")
    return member


# ---------------------------------------------------------------------------
# Project operations
# ---------------------------------------------------------------------------

def create_project(
    db: Session, *, org_id: str, user_id: str, name: str, description: str | None = None
) -> Project:
    """Create a new project inside an organization."""
    _require_write_access(db, org_id, user_id)

    project = repo.create_project(
        db,
        project_id=str(uuid.uuid4()),
        organization_id=org_id,
        name=name,
        description=description,
        created_by=user_id,
    )
    record_audit_event(
        db,
        organization_id=org_id,
        user_id=user_id,
        action="PROJECT_CREATED",
        resource_type="project",
        resource_id=project.id,
    )
    db.commit()
    db.refresh(project)

    log_security_event(
        "PROJECT_CREATED",
        user_id=user_id,
        detail=f"Created project '{name}' in org {org_id}",
    )
    logger.info(f"Project created: {project.id} by user {user_id}")
    return project


def get_project(db: Session, project_id: str, user_id: str) -> Project:
    """
    Get a project by ID. Verifies the caller is a member of the
    project's organization.
    """
    project = repo.get_project_by_id(db, project_id)
    if project is None:
        raise ResourceNotFound("Project")
    _require_membership(db, project.organization_id, user_id)
    return project


def require_project_write_access(db: Session, project_id: str, user_id: str) -> Project:
    """Return a project after verifying that the user may modify it."""
    project = repo.get_project_by_id(db, project_id)
    if project is None:
        raise ResourceNotFound("Project")
    _require_write_access(db, project.organization_id, user_id)
    return project


def list_projects(
    db: Session,
    *,
    org_id: str,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
) -> tuple[list[Project], int]:
    """List projects in an organization with pagination."""
    _require_membership(db, org_id, user_id)
    return repo.list_projects(db, org_id, page=page, page_size=page_size, search=search)


def update_project(
    db: Session,
    *,
    project_id: str,
    user_id: str,
    name: str | None = None,
    description: str | None = None,
) -> Project:
    """Update a project's details."""
    project = repo.get_project_by_id(db, project_id)
    if project is None:
        raise ResourceNotFound("Project")
    _require_write_access(db, project.organization_id, user_id)

    changed_fields = [
        field
        for field, value, current in (
            ("name", name, project.name),
            ("description", description, project.description),
        )
        if value is not None and value != current
    ]
    updated = repo.update_project(db, project, name=name, description=description)
    if changed_fields:
        record_audit_event(
            db,
            organization_id=project.organization_id,
            user_id=user_id,
            action="PROJECT_UPDATED",
            resource_type="project",
            resource_id=project_id,
            metadata={"changed_fields": changed_fields},
        )
    db.commit()
    db.refresh(updated)

    log_security_event(
        "PROJECT_UPDATED",
        user_id=user_id,
        detail=f"Updated project {project_id}",
    )
    return updated


def delete_project(db: Session, *, project_id: str, user_id: str) -> None:
    """
    Delete a project. Requires OWNER or ADMIN role.
    """
    project = repo.get_project_by_id(db, project_id)
    if project is None:
        raise ResourceNotFound("Project")

    member = _require_membership(db, project.organization_id, user_id)
    if member.role not in (OrgRole.OWNER, OrgRole.ADMIN):
        raise PermissionDenied("Only owners and admins can delete projects.")

    organization_id = project.organization_id
    record_audit_event(
        db,
        organization_id=organization_id,
        user_id=user_id,
        action="PROJECT_DELETED",
        resource_type="project",
        resource_id=project_id,
    )
    repo.delete_project(db, project)
    db.commit()

    log_security_event(
        "PROJECT_DELETED",
        user_id=user_id,
        detail=f"Deleted project {project_id} from org {project.organization_id}",
    )
    logger.info(f"Project deleted: {project_id} by user {user_id}")


def get_project_summary(db: Session, *, project_id: str, user_id: str) -> dict:
    """
    Get project summary with counts for persisted project resources.

    Chat conversations are shared with all members of the project.
    """
    project = get_project(db, project_id, user_id)
    return {
        "project_id": project.id,
        "name": project.name,
        "document_count": (
            db.query(ProjectDocument)
            .filter(ProjectDocument.project_id == project.id)
            .count()
        ),
        "conversation_count": (
            db.query(Conversation)
            .filter(Conversation.project_id == project.id)
            .count()
        ),
        "report_count": (
            db.query(ResearchReport)
            .filter(ResearchReport.project_id == project.id)
            .count()
        ),
    }
