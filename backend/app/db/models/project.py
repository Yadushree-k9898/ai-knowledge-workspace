"""
Project database model.

A project is a knowledge workspace inside an organization.
Documents, conversations, and reports all belong to a project.

Example hierarchy:
    Acme (Organization)
     ├── Market Research (Project)
     ├── Competitor Analysis (Project)
     └── Product Research (Project)
"""

from sqlalchemy import Column, String, DateTime, func, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True)

    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # The user who created this project (profile.id / Supabase UUID)
    created_by = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    organization = relationship("Organization", backref="projects")
    document_links = relationship(
        "ProjectDocument", back_populates="project", cascade="all, delete-orphan"
    )
    comparisons = relationship(
        "ProjectComparison", back_populates="project", cascade="all, delete-orphan"
    )
    reports = relationship(
        "ResearchReport", back_populates="project", cascade="all, delete-orphan"
    )
    conversations = relationship(
        "Conversation", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name!r} org={self.organization_id}>"
