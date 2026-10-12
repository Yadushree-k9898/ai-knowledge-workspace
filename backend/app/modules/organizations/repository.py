"""
Organizations repository — database access layer.

All SQL queries for Organization, OrganizationMember, and
OrganizationInvitation tables live here.
Business logic belongs in service.py, not here.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.db.models.organization import Organization
from app.db.models.organization_member import OrganizationMember, OrgRole
from app.db.models.organization_invitation import OrganizationInvitation


# ---------------------------------------------------------------------------
# Organization CRUD
# ---------------------------------------------------------------------------

def create_organization(db: Session, *, org_id: str, name: str, slug: str, owner_id: str) -> Organization:
    """Create a new organization row."""
    org = Organization(id=org_id, name=name, slug=slug, owner_id=owner_id)
    db.add(org)
    db.flush()  # flush so we can use org.id; caller commits the transaction
    return org


def get_organization_by_id(db: Session, org_id: str) -> Organization | None:
    """Fetch an organization by primary key."""
    return db.query(Organization).filter(Organization.id == org_id).first()


def get_organization_by_slug(db: Session, slug: str) -> Organization | None:
    """Fetch an organization by its URL slug."""
    return db.query(Organization).filter(Organization.slug == slug).first()


def get_organizations_for_user(db: Session, user_id: str) -> list[dict]:
    """
    Return all organizations a user belongs to, including their role.
    Joins organization_members → organizations.
    """
    rows = (
        db.query(Organization, OrganizationMember.role)
        .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
        .filter(OrganizationMember.user_id == user_id)
        .order_by(Organization.name)
        .all()
    )
    return [{"organization": org, "role": role} for org, role in rows]


def update_organization(db: Session, org: Organization, *, name: str | None = None) -> Organization:
    """Update mutable organization fields. Only provided values are changed."""
    if name is not None:
        org.name = name
    db.flush()
    db.refresh(org)
    return org


def delete_organization(db: Session, org: Organization) -> None:
    """Hard-delete an organization. Cascade will remove members + invitations."""
    db.delete(org)
    db.flush()


# ---------------------------------------------------------------------------
# Member CRUD
# ---------------------------------------------------------------------------

def create_member(
    db: Session, *, member_id: str, organization_id: str, user_id: str, role: OrgRole
) -> OrganizationMember:
    """Create a new membership row."""
    member = OrganizationMember(
        id=member_id,
        organization_id=organization_id,
        user_id=user_id,
        role=role,
    )
    db.add(member)
    db.flush()
    return member


def get_member(db: Session, organization_id: str, user_id: str) -> OrganizationMember | None:
    """Find a specific membership by org + user."""
    return (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
        .first()
    )


def get_member_by_id(db: Session, member_id: str) -> OrganizationMember | None:
    """Find a membership by its primary key."""
    return db.query(OrganizationMember).filter(OrganizationMember.id == member_id).first()


def list_members(db: Session, organization_id: str) -> list[OrganizationMember]:
    """Return all members of an organization."""
    return (
        db.query(OrganizationMember)
        .filter(OrganizationMember.organization_id == organization_id)
        .order_by(OrganizationMember.joined_at)
        .all()
    )


def update_member_role(db: Session, member: OrganizationMember, role: OrgRole) -> OrganizationMember:
    """Change a member's role."""
    member.role = role
    db.flush()
    db.refresh(member)
    return member


def delete_member(db: Session, member: OrganizationMember) -> None:
    """Remove a member from the organization."""
    db.delete(member)
    db.flush()


# ---------------------------------------------------------------------------
# Invitation CRUD
# ---------------------------------------------------------------------------

def create_invitation(
    db: Session,
    *,
    invitation_id: str,
    organization_id: str,
    email: str,
    role: OrgRole,
    token: str,
    invited_by: str,
    expires_at: datetime,
) -> OrganizationInvitation:
    """Create a new invitation row."""
    invitation = OrganizationInvitation(
        id=invitation_id,
        organization_id=organization_id,
        email=email,
        role=role,
        token=token,
        invited_by=invited_by,
        expires_at=expires_at,
    )
    db.add(invitation)
    db.flush()
    return invitation


def get_invitation_by_token(db: Session, token: str) -> OrganizationInvitation | None:
    """Fetch an invitation by its unique accept token."""
    return (
        db.query(OrganizationInvitation)
        .filter(OrganizationInvitation.token == token)
        .first()
    )


def get_pending_invitation(db: Session, organization_id: str, email: str) -> OrganizationInvitation | None:
    """Find a pending (not yet accepted) invitation for a specific email + org."""
    return (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.organization_id == organization_id,
            OrganizationInvitation.email == email,
            OrganizationInvitation.accepted_at.is_(None),
        )
        .first()
    )


def mark_invitation_accepted(db: Session, invitation: OrganizationInvitation) -> OrganizationInvitation:
    """Mark an invitation as accepted with current timestamp."""
    invitation.accepted_at = datetime.now(timezone.utc)
    db.flush()
    db.refresh(invitation)
    return invitation
