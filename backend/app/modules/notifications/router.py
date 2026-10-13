"""Authenticated notification inbox endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.notifications import service
from app.modules.notifications.schemas import (
    NotificationEnvelope,
    NotificationListResponse,
    NotificationResponse,
)

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListResponse, summary="List notifications")
async def list_notifications(
    unread_only: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notifications = service.list_notifications(
        db,
        user_id=user["id"],
        email=user.get("email"),
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    return {"data": [NotificationResponse.model_validate(item) for item in notifications]}


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationEnvelope,
    summary="Mark a notification as read",
)
async def mark_notification_read(
    notification_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = service.set_notification_read(
        db,
        notification_id=notification_id,
        user_id=user["id"],
        email=user.get("email"),
        is_read=True,
    )
    return {"data": NotificationResponse.model_validate(notification)}


@router.patch(
    "/{notification_id}/unread",
    response_model=NotificationEnvelope,
    summary="Mark a notification as unread",
)
async def mark_notification_unread(
    notification_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = service.set_notification_read(
        db,
        notification_id=notification_id,
        user_id=user["id"],
        email=user.get("email"),
        is_read=False,
    )
    return {"data": NotificationResponse.model_validate(notification)}