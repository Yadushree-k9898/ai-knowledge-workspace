"""Append-only organization audit events."""

from sqlalchemy import Column, DateTime, Index, JSON, String, func

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_org_timestamp", "organization_id", "timestamp"),
        Index("ix_audit_logs_org_action", "organization_id", "action"),
        Index("ix_audit_logs_org_resource", "organization_id", "resource_type"),
    )

    id = Column(String, primary_key=True, index=True)
    organization_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(255), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    event_metadata = Column("metadata", JSON, nullable=False, default=dict)