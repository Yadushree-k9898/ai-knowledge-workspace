"""
Organizations dependencies — FastAPI dependency injection for org-scoped endpoints.

Provides:
  - require_org_member: verifies user belongs to the organization
  - require_org_role: verifies user has a specific role in the organization
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.organization_member import OrgRole
from app.core.exceptions import PermissionDenied
from app.modules.auth.dependencies import get_current_user
from app.modules.organizations import repository as repo


def require_org_member(
    organization_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    FastAPI dependency that verifies the current user is a member
    of the given organization. Returns the membership record.
    """
    member = repo.get_member(db, organization_id, user["id"])
    if member is None:
        raise PermissionDenied("You are not a member of this organization.")
    return member


def require_org_role(*allowed_roles: OrgRole):
    """
    Factory that returns a FastAPI dependency verifying the user
    has one of the allowed roles in the organization.

    Usage:
        @router.delete("/{organization_id}", dependencies=[Depends(require_org_role(OrgRole.OWNER))])
    """
    def dependency(
        organization_id: str,
        user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        member = repo.get_member(db, organization_id, user["id"])
        if member is None:
            raise PermissionDenied("You are not a member of this organization.")
        if member.role not in allowed_roles:
            raise PermissionDenied(
                f"This action requires one of: {', '.join(r.value for r in allowed_roles)}."
            )
        return member
    return dependency
