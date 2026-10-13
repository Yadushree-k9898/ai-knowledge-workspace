from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pytest

from app.core.exceptions import ResourceNotFound
from app.db.base import Base
from app.db.models.notification import Notification
from app.modules.notifications.service import (
    create_notification,
    list_notifications,
    set_notification_read,
)


@pytest.fixture
def notification_db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine, tables=[Notification.__table__])
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine, tables=[Notification.__table__])
        engine.dispose()


def test_list_notifications_scopes_direct_and_invitation_notifications(notification_db):
    own = create_notification(
        notification_db,
        user_id="user-1",
        notification_type="REPORT_READY",
        title="Report ready",
        message="Your report is ready.",
    )
    invited = create_notification(
        notification_db,
        recipient_email="Invitee@Example.com",
        notification_type="INVITATION_RECEIVED",
        title="Invitation",
        message="You were invited.",
    )
    create_notification(
        notification_db,
        user_id="user-2",
        notification_type="REPORT_READY",
        title="Private report",
        message="Another user's report.",
    )
    notification_db.commit()

    rows = list_notifications(
        notification_db,
        user_id="user-1",
        email="invitee@example.com",
        unread_only=False,
        limit=100,
        offset=0,
    )

    assert {row.id for row in rows} == {own.id, invited.id}
    assert notification_db.get(Notification, invited.id).user_id == "user-1"
    assert notification_db.get(Notification, invited.id).recipient_email is None


def test_list_notifications_filters_unread_and_paginates(notification_db):
    first = create_notification(
        notification_db,
        user_id="user-1",
        notification_type="DOCUMENT_PROCESSED",
        title="First",
        message="Done.",
    )
    second = create_notification(
        notification_db,
        user_id="user-1",
        notification_type="DOCUMENT_PROCESSED",
        title="Second",
        message="Done.",
    )
    notification_db.commit()
    set_notification_read(
        notification_db,
        notification_id=first.id,
        user_id="user-1",
        email=None,
        is_read=True,
    )

    rows = list_notifications(
        notification_db,
        user_id="user-1",
        email=None,
        unread_only=True,
        limit=1,
        offset=0,
    )

    assert [row.id for row in rows] == [second.id]


def test_mark_read_and_unread_and_prevent_cross_user_access(notification_db):
    notification = create_notification(
        notification_db,
        user_id="user-1",
        notification_type="REPORT_READY",
        title="Report ready",
        message="Done.",
    )
    notification_db.commit()

    read = set_notification_read(
        notification_db,
        notification_id=notification.id,
        user_id="user-1",
        email=None,
        is_read=True,
    )
    assert read.read_at is not None

    unread = set_notification_read(
        notification_db,
        notification_id=notification.id,
        user_id="user-1",
        email=None,
        is_read=False,
    )
    assert unread.read_at is None

    with pytest.raises(ResourceNotFound):
        set_notification_read(
            notification_db,
            notification_id=notification.id,
            user_id="user-2",
            email=None,
            is_read=True,
        )
