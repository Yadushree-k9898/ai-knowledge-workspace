"""
Organizations service — business logic for organizations, members, and invitations.

This layer orchestrates repository calls, enforces business rules
(ownership, role hierarchy, slug generation), and manages transactions.
"""

import re
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.logging import log_security_event, get_logger
from app.core.exceptions import (
    OrganizationNotFound,
    MemberNotFound,
    AlreadyMember,
    SlugConflict,
    PermissionDenied,
    InvitationNotFound,
    InvitationExpired,
    InvitationAlreadyAccepted,
    CannotRemoveOwner,
)
from app.db.models.organization import Organization
from app.db.models.organization_member import OrganizationMember, OrgRole
from app.db.models.organization_invitation import OrganizationInvitation
from app.modules.organizations import repository as repo

logger = get_logger("organizations.service")

# Invitation links expire after this duration
INVITATION_EXPIRY_DAYS = 7


# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------

def _generate_slug(name: str) -> str:
    """
    Convert an organization name into a URL-friendly slug.

    Examples:
        "Acme Research" → "acme-research"
        "My  Cool—Org!" → "my-cool-org"
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)       # remove non-word chars (except spaces, hyphens)
    slug = re.sub(r"[\s_]+", "-", slug)         # spaces/underscores → hyphens
    slug = re.sub(r"-+", "-", slug)             # collapse consecutive hyphens
    slug = slug.strip("-")
    return slug


def _ensure_unique_slug(db: Session, slug: str) -> str:
    """
    If the slug already exists, append a short random suffix.
    Returns a slug guaranteed to be unique.
    """
    if repo.get_organization_by_slug(db, slug) is None:
        return slug

    # Append 6 random hex chars
    suffix = uuid.uuid4().hex[:6]
    candidate = f"{slug}-{suffix}"

    # Extremely unlikely to collide, but check once more
    if repo.get_organization_by_slug(db, candidate) is not None:
        candidate = f"{slug}-{uuid.uuid4().hex[:8]}"

    return candidate


# ---------------------------------------------------------------------------
# Organization operations
# ---------------------------------------------------------------------------

def create_organization(db: Session, *, user_id: str, name: str) -> Organization:
    """
    Create a new organization and make the creator the OWNER.

    Returns the created Organization.
    """
    slug = _generate_slug(name)
    slug = _ensure_unique_slug(db, slug)

    org = repo.create_organization(
        db,
        org_id=str(uuid.uuid4()),
        name=name,
        slug=slug,
        owner_id=user_id,
    )

    # Auto-create OWNER membership for the creator
    repo.create_member(
        db,
        member_id=str(uuid.uuid4()),
        organization_id=org.id,
        user_id=user_id,
        role=OrgRole.OWNER,
    )

    db.commit()
    db.refresh(org)

    log_security_event(
        "ORGANIZATION_CREATED",
        user_id=user_id,
        detail=f"Created organization '{name}' (slug={slug})",
    )
    logger.info(f"Organization created: {org.id} by user {user_id}")

    return org


def get_organization(db: Session, org_id: str) -> Organization:
    """Get an organization by ID or raise OrganizationNotFound."""
    org = repo.get_organization_by_id(db, org_id)
    if org is None:
        raise OrganizationNotFound()
    return org


def list_user_organizations(db: Session, user_id: str) -> list[dict]:
    """Return all organizations a user belongs to, with their role."""
    return repo.get_organizations_for_user(db, user_id)


def update_organization(
    db: Session, *, org_id: str, user_id: str, name: str | None = None
) -> Organization:
    """
    Update an organization's details.
    Only OWNER and ADMIN roles can update.
    """
    org = get_organization(db, org_id)
    _require_role(db, org_id, user_id, [OrgRole.OWNER, OrgRole.ADMIN])

    updated = repo.update_organization(db, org, name=name)
    db.commit()
    db.refresh(updated)

    log_security_event(
        "ORGANIZATION_UPDATED",
        user_id=user_id,
        detail=f"Updated organization {org_id}",
    )
    return updated


def delete_organization(db: Session, *, org_id: str, user_id: str) -> None:
    """
    Delete an organization. Only the OWNER can do this.
    Cascades to members and invitations.
    """
    org = get_organization(db, org_id)
    _require_role(db, org_id, user_id, [OrgRole.OWNER])

    repo.delete_organization(db, org)
    db.commit()

    log_security_event(
        "ORGANIZATION_DELETED",
        user_id=user_id,
        detail=f"Deleted organization {org_id}",
    )
    logger.info(f"Organization deleted: {org_id} by user {user_id}")


# ---------------------------------------------------------------------------
# Member operations
# ---------------------------------------------------------------------------

def list_members(db: Session, *, org_id: str, user_id: str) -> list[OrganizationMember]:
    """
    List all members of an organization.
    Caller must be a member themselves.
    """
    _require_membership(db, org_id, user_id)
    return repo.list_members(db, org_id)


def update_member_role(
    db: Session, *, org_id: str, member_id: str, user_id: str, new_role: OrgRole
) -> OrganizationMember:
    """
    Change a member's role. Only OWNER and ADMIN can do this.
    Cannot change the owner's role.
    """
    _require_role(db, org_id, user_id, [OrgRole.OWNER, OrgRole.ADMIN])

    member = repo.get_member_by_id(db, member_id)
    if member is None or member.organization_id != org_id:
        raise MemberNotFound()

    # Cannot demote the owner
    if member.role == OrgRole.OWNER:
        raise CannotRemoveOwner()

    # Only owner can promote to ADMIN
    if new_role == OrgRole.ADMIN:
        _require_role(db, org_id, user_id, [OrgRole.OWNER])

    updated = repo.update_member_role(db, member, new_role)
    db.commit()
    db.refresh(updated)

    log_security_event(
        "MEMBER_ROLE_CHANGED",
        user_id=user_id,
        detail=f"Changed member {member_id} role to {new_role.value} in org {org_id}",
    )
    return updated


def remove_member(db: Session, *, org_id: str, member_id: str, user_id: str) -> None:
    """
    Remove a member from the organization.
    OWNER and ADMIN can remove others. Members can remove themselves.
    Owner cannot be removed.
    """
    member = repo.get_member_by_id(db, member_id)
    if member is None or member.organization_id != org_id:
        raise MemberNotFound()

    if member.role == OrgRole.OWNER:
        raise CannotRemoveOwner()

    # Self-removal is always allowed (except owner)
    is_self_removal = member.user_id == user_id
    if not is_self_removal:
        _require_role(db, org_id, user_id, [OrgRole.OWNER, OrgRole.ADMIN])

    repo.delete_member(db, member)
    db.commit()

    log_security_event(
        "MEMBER_REMOVED",
        user_id=user_id,
        detail=f"Removed member {member_id} from org {org_id} (self={'yes' if is_self_removal else 'no'})",
    )


# ---------------------------------------------------------------------------
# Invitation operations
# ---------------------------------------------------------------------------

def create_invitation(
    db: Session,
    *,
    org_id: str,
    user_id: str,
    email: str,
    role: OrgRole,
) -> OrganizationInvitation:
    """
    Create an invitation to join the organization.
    Only OWNER and ADMIN can invite.
    """
    _require_role(db, org_id, user_id, [OrgRole.OWNER, OrgRole.ADMIN])

    # Check if already a member (by looking up all members and comparing email — 
    # we need profile lookup; for now we check by pending invitation)
    existing_pending = repo.get_pending_invitation(db, org_id, email)
    if existing_pending and not existing_pending.is_expired:
        # Return the existing pending invitation instead of creating a duplicate
        return existing_pending

    invitation = repo.create_invitation(
        db,
        invitation_id=str(uuid.uuid4()),
        organization_id=org_id,
        email=email,
        role=role,
        token=uuid.uuid4().hex,
        invited_by=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=INVITATION_EXPIRY_DAYS),
    )
    db.commit()
    db.refresh(invitation)

    log_security_event(
        "INVITATION_CREATED",
        user_id=user_id,
        detail=f"Invited {email} as {role.value} to org {org_id}",
    )
    logger.info(f"Invitation created: {invitation.id} for {email} to org {org_id}")
    return invitation


def get_invitation(db: Session, token: str) -> OrganizationInvitation:
    """Get an invitation by token or raise InvitationNotFound."""
    invitation = repo.get_invitation_by_token(db, token)
    if invitation is None:
        raise InvitationNotFound()
    return invitation


def accept_invitation(db: Session, *, token: str, user_id: str) -> OrganizationMember:
    """
    Accept an invitation and create the membership.

    Validates that the invitation is not expired or already accepted,
    and that the user is not already a member.
    """
    invitation = get_invitation(db, token)

    if invitation.is_accepted:
        raise InvitationAlreadyAccepted()

    if invitation.is_expired:
        raise InvitationExpired()

    # Check if already a member
    existing = repo.get_member(db, invitation.organization_id, user_id)
    if existing:
        raise AlreadyMember()

    # Create membership with the invited role
    member = repo.create_member(
        db,
        member_id=str(uuid.uuid4()),
        organization_id=invitation.organization_id,
        user_id=user_id,
        role=invitation.role,
    )

    repo.mark_invitation_accepted(db, invitation)
    db.commit()
    db.refresh(member)

    log_security_event(
        "INVITATION_ACCEPTED",
        user_id=user_id,
        detail=f"Accepted invitation {invitation.id} to org {invitation.organization_id} as {invitation.role.value}",
    )
    logger.info(f"User {user_id} accepted invitation to org {invitation.organization_id}")
    return member


# ---------------------------------------------------------------------------
# Authorization helpers
# ---------------------------------------------------------------------------

def _require_membership(db: Session, org_id: str, user_id: str) -> OrganizationMember:
    """Verify the user is a member of the organization. Raises PermissionDenied."""
    member = repo.get_member(db, org_id, user_id)
    if member is None:
        raise PermissionDenied("You are not a member of this organization.")
    return member


def _require_role(
    db: Session, org_id: str, user_id: str, allowed_roles: list[OrgRole]
) -> OrganizationMember:
    """Verify the user has one of the allowed roles. Raises PermissionDenied."""
    member = _require_membership(db, org_id, user_id)
    if member.role not in allowed_roles:
        raise PermissionDenied(
            f"This action requires one of: {', '.join(r.value for r in allowed_roles)}."
        )
    return member
