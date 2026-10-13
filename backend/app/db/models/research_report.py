"""Persisted project research reports and their generation state."""

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id = Column(String, primary_key=True, index=True)
    project_id = Column(
        String,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by = Column(String, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    report_type = Column(String(40), nullable=False)
    instructions = Column(Text, nullable=True)
    source_document_ids = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False, default="QUEUED", index=True)
    content = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project = relationship("Project", back_populates="reports")