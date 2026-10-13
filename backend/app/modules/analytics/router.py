"""Organization-level analytics endpoints."""

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.analytics import service
from app.modules.analytics.schemas import (
    OrganizationAnalyticsEnvelope,
    OrganizationAnalyticsResponse,
)
from app.modules.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/organizations", tags=["Analytics"])


@router.get(
    "/{organization_id}/analytics",
    response_model=OrganizationAnalyticsEnvelope,
    summary="Get organization analytics",
)
async def get_organization_analytics(
    organization_id: str,
    date_from: date = Query(
        default_factory=lambda: datetime.now(timezone.utc).date() - timedelta(days=29)
    ),
    date_to: date = Query(default_factory=lambda: datetime.now(timezone.utc).date()),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analytics = service.get_organization_analytics(
        db,
        organization_id=organization_id,
        user_id=user["id"],
        date_from=date_from,
        date_to=date_to,
    )
    return {"data": OrganizationAnalyticsResponse(**analytics)}