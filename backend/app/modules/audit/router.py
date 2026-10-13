from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.audit import service
from app.modules.audit.schemas import (
    AuditLogListResponse,
    AuditLogPagination,
    AuditLogResponse,
)
from app.modules.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/organizations", tags=["Audit Logs"])


@router.get(
    "/{organization_id}/audit-logs",
    response_model=AuditLogListResponse,
    summary="List organization audit events",
)
async def list_organization_audit_logs(
    organization_id: str,
    action: str | None = Query(default=None, min_length=1, max_length=100),
    resource_type: str | None = Query(default=None, min_length=1, max_length=50),
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    events, total = service.list_audit_logs(
        db,
        organization_id=organization_id,
        user_id=user["id"],
        action=action,
        resource_type=resource_type,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )
    return {
        "data": [
            AuditLogResponse(
                id=event.id,
                organization_id=event.organization_id,
                user_id=event.user_id,
                action=event.action,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                timestamp=event.timestamp,
                metadata=event.event_metadata,
            )
            for event in events
        ],
        "pagination": AuditLogPagination(limit=limit, offset=offset, total=total),
    }