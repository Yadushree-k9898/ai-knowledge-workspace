"""
OrganizationMember database model.

Links a user (profile) to an organization with a specific role.
This is the junction table that makes multi-tenancy work — a user
can belong to multiple organizations, and an organization has many members.

Roles: OWNER, ADMIN, MEMBER, VIEWER
"""

import enum

from sqlalchemy import Column, String, DateTime, func, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class OrgRole(str, enum.Enum):
    """Organization membership roles, ordered by privilege level."""
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = Column(String, primary_key=True, index=True)

    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(String, nullable=False, index=True)
    role = Column(Enum(OrgRole, name="org_role"), nullable=False, default=OrgRole.MEMBER)

    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # --- Constraints ---
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member_user"),
    )

    # --- Relationships ---
    organization = relationship("Organization", back_populates="members")

    def __repr__(self) -> str:
        return (
            f"<OrganizationMember id={self.id} "
            f"org={self.organization_id} user={self.user_id} role={self.role}>"
        )
