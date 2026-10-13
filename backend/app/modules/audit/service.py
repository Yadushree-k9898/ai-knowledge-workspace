"""Audit event persistence and access-controlled organization queries."""

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDenied, ValidationError
from app.db.models.audit_log import AuditLog
from app.db.models.organization_member import OrgRole
from app.modules.organizations import repository as organization_repository

_SENSITIVE_AUDIT_KEYS = {
    "access_token",
    "refresh_token",
    "token",
    "secret",
    "password",
    "authorization",
    "cookie",
    "jwt",
    "email",
    "invitation_token",
    "api_key",
    "client_secret",
}


def _sanitize_audit_metadata(value: Any) -> Any:
    """Strip sensitive fields or values from metadata before persisting it."""
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            normalized_key = str(key).lower()
            if normalized_key in _SENSITIVE_AUDIT_KEYS:
                continue
            sanitized[str(key)] = _sanitize_audit_metadata(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_audit_metadata(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_audit_metadata(item) for item in value)
    return value


def record_audit_event(
    db: Session,
    *,
    organization_id: str,
    user_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Add an audit event to the current transaction without committing it."""
    sanitized_metadata = _sanitize_audit_metadata(metadata or {})
    event = AuditLog(
        id=str(uuid.uuid4()),
        organization_id=organization_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        event_metadata=sanitized_metadata,
    )
    db.add(event)
    return event


def list_audit_logs(
    db: Session,
    *,
    organization_id: str,
    user_id: str,
    action: str | None = None,
    resource_type: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AuditLog], int]:
    membership = organization_repository.get_member(db, organization_id, user_id)
    if membership is None or membership.role not in (OrgRole.OWNER, OrgRole.ADMIN):
        raise PermissionDenied("Only organization owners and admins can view audit logs.")
    if since is not None and until is not None and since > until:
        raise ValidationError("since must be on or before until.")

    query = db.query(AuditLog).filter(AuditLog.organization_id == organization_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if since is not None:
        query = query.filter(AuditLog.timestamp >= since)
    if until is not None:
        query = query.filter(AuditLog.timestamp <= until)

    total = query.count()
    events = (
        query.order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return events, total