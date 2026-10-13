from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    user_id: str | None
    action: str
    resource_type: str
    resource_id: str
    timestamp: datetime
    metadata: dict[str, Any]


class AuditLogPagination(BaseModel):
    limit: int
    offset: int
    total: int


class AuditLogListResponse(BaseModel):
    data: list[AuditLogResponse]
    pagination: AuditLogPagination