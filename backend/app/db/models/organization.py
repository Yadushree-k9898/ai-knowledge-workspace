"""
Organization database model.

Represents a tenant in the multi-tenant system.
Each organization has a unique slug for URL-friendly identification,
an owner (the user who created it), and timestamps.
"""

from sqlalchemy import Column, String, DateTime, func, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)

    # The user who created this organization (profile.id / Supabase UUID)
    owner_id = Column(String, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    members = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    invitations = relationship(
        "OrganizationInvitation",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Organization id={self.id} name={self.name!r} slug={self.slug!r}>"
