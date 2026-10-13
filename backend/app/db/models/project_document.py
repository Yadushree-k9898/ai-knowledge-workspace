"""Links uploaded documents to projects without duplicating document content."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class ProjectDocument(Base):
    __tablename__ = "project_documents"

    project_id = Column(
        String,
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    )
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    added_by = Column(String, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="document_links")
    document = relationship("Document", back_populates="project_links")
