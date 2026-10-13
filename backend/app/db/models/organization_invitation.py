"""
OrganizationInvitation database model.

Tracks pending invitations for users to join an organization.
Each invitation has a unique token used in the accept URL,
an expiry time, and optional accepted_at timestamp.
"""

from sqlalchemy import Column, String, DateTime, func, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.models.organization_member import OrgRole


class OrganizationInvitation(Base):
    __tablename__ = "organization_invitations"

    id = Column(String, primary_key=True, index=True)

    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Email of the person being invited (may or may not have an account yet)
    email = Column(String(320), nullable=False, index=True)

    # Role the invitee will receive upon accepting
    role = Column(Enum(OrgRole, name="org_role", create_type=False), nullable=False, default=OrgRole.MEMBER)

    # Unique token for the invitation URL (e.g., /invitations/<token>)
    token = Column(String, unique=True, nullable=False, index=True)

    # Who sent this invitation (profile.id / Supabase UUID)
    invited_by = Column(String, nullable=False)

    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # --- Relationships ---
    organization = relationship("Organization", back_populates="invitations")

    @property
    def is_expired(self) -> bool:
        """Check if the invitation has passed its expiry time."""
        from datetime import datetime, timezone
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expires_at

    @property
    def is_accepted(self) -> bool:
        """Check if the invitation has already been accepted."""
        return self.accepted_at is not None

    def __repr__(self) -> str:
        return (
            f"<OrganizationInvitation id={self.id} "
            f"org={self.organization_id} email={self.email!r} role={self.role}>"
        )
