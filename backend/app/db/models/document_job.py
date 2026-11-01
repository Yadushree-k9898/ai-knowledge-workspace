"""Durable background-processing state for uploaded project documents."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, String, Text, func
from app.db.base import Base


class DocumentJob(Base):
    __tablename__ = "document_jobs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by = Column(String, nullable=False, index=True)
    file_data = Column(LargeBinary, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
