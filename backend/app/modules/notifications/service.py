"""Notification persistence, recipient scoping, and read-state operations."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFound
from app.db.models.notification import Notification


def create_notification(
    db: Session,
    *,
    notification_type: str,
    title: str,
    message: str,
    user_id: str | None = None,
    recipient_email: str | None = None,
    link: str | None = None,
) -> Notification:
    if (user_id is None) == (recipient_email is None):
        raise ValueError("A notification must have exactly one recipient.")

    notification = Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        recipient_email=recipient_email.strip().lower() if recipient_email else None,
        type=notification_type,
        title=title,
        message=message,
        link=link,
    )
    db.add(notification)
    db.flush()
    return notification


def list_notifications(
    db: Session,
    *,
    user_id: str,
    email: str | None,
    unread_only: bool,
    limit: int,
    offset: int,
) -> list[Notification]:
    recipient_filter = Notification.user_id == user_id
    normalized_email = email.strip().lower() if email else None
    if normalized_email:
        recipient_filter = or_(
            recipient_filter,
            (
                (Notification.user_id.is_(None))
                & (func.lower(Notification.recipient_email) == normalized_email)
            ),
        )

    query = db.query(Notification).filter(recipient_filter)
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))

    notifications = (
        query.order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    claimed = False
    if normalized_email:
        for notification in notifications:
            if notification.user_id is None:
                notification.user_id = user_id
                notification.recipient_email = None
                claimed = True
    if claimed:
        db.commit()

    return notifications


def set_notification_read(
    db: Session,
    *,
    notification_id: str,
    user_id: str,
    email: str | None,
    is_read: bool,
) -> Notification:
    query = db.query(Notification).filter(Notification.id == notification_id)
    notification = query.filter(Notification.user_id == user_id).first()
    if notification is None and email:
        notification = query.filter(
            Notification.user_id.is_(None),
            func.lower(Notification.recipient_email) == email.strip().lower(),
        ).first()
        if notification is not None:
            notification.user_id = user_id
            notification.recipient_email = None

    if notification is None:
        raise ResourceNotFound("Notification")

    notification.read_at = datetime.now(timezone.utc) if is_read else None
    db.commit()
    db.refresh(notification)
    return notification