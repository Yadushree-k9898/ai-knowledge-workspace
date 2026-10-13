from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import PermissionDenied, ValidationError
from app.db.base import Base
from app.db.models.audit_log import AuditLog
from app.db.models.organization import Organization
from app.db.models.organization_invitation import OrganizationInvitation
from app.db.models.organization_member import OrganizationMember, OrgRole
from app.db.models.project import Project
from app.modules.audit.service import list_audit_logs, record_audit_event
from app.modules.organizations.service import create_organization, delete_organization


@pytest.fixture
def audit_db():
    engine = create_engine("sqlite://")
    tables = [
        Organization.__table__,
        OrganizationMember.__table__,
        OrganizationInvitation.__table__,
        Project.__table__,
        AuditLog.__table__,
    ]
    Base.metadata.create_all(engine, tables=tables)
    db = sessionmaker(bind=engine)()
    db.add(
        Organization(
            id="org-1",
            name="Research",
            slug="research",
            owner_id="owner-1",
        )
    )
    db.add_all(
        [
            OrganizationMember(
                id="owner-member",
                organization_id="org-1",
                user_id="owner-1",
                role=OrgRole.OWNER,
            ),
            OrganizationMember(
                id="admin-member",
                organization_id="org-1",
                user_id="admin-1",
                role=OrgRole.ADMIN,
            ),
            OrganizationMember(
                id="member-member",
                organization_id="org-1",
                user_id="member-1",
                role=OrgRole.MEMBER,
            ),
            OrganizationMember(
                id="viewer-member",
                organization_id="org-1",
                user_id="viewer-1",
                role=OrgRole.VIEWER,
            ),
        ]
    )
    now = datetime.now(timezone.utc)
    db.add_all(
        [
            AuditLog(
                id="event-a",
                organization_id="org-1",
                user_id="owner-1",
                action="PROJECT_CREATED",
                resource_type="project",
                resource_id="project-a",
                timestamp=now - timedelta(minutes=1),
                event_metadata={},
            ),
            AuditLog(
                id="event-b",
                organization_id="org-1",
                user_id="admin-1",
                action="PROJECT_UPDATED",
                resource_type="project",
                resource_id="project-b",
                timestamp=now,
                event_metadata={"changed_fields": ["name"]},
            ),
            AuditLog(
                id="other-org-event",
                organization_id="org-2",
                user_id="other-user",
                action="PROJECT_CREATED",
                resource_type="project",
                resource_id="project-c",
                timestamp=now,
                event_metadata={},
            ),
        ]
    )
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine, tables=tables)
        engine.dispose()


def test_list_audit_logs_filters_paginates_and_scopes_to_organization(audit_db):
    events, total = list_audit_logs(
        audit_db,
        organization_id="org-1",
        user_id="owner-1",
        resource_type="project",
        limit=1,
        offset=0,
    )

    assert total == 2
    assert len(events) == 1
    assert events[0].id == "event-b"
    assert events[0].event_metadata == {"changed_fields": ["name"]}


def test_list_audit_logs_filters_by_action_and_time(audit_db):
    events, total = list_audit_logs(
        audit_db,
        organization_id="org-1",
        user_id="admin-1",
        action="PROJECT_CREATED",
        since=datetime.now(timezone.utc) - timedelta(minutes=2),
        until=datetime.now(timezone.utc),
    )

    assert total == 1
    assert events[0].id == "event-a"


@pytest.mark.parametrize("user_id", ["member-1", "viewer-1", "outsider"])
def test_list_audit_logs_denies_non_admin_members(audit_db, user_id):
    with pytest.raises(PermissionDenied):
        list_audit_logs(
            audit_db,
            organization_id="org-1",
            user_id=user_id,
        )


def test_list_audit_logs_rejects_reversed_time_range(audit_db):
    with pytest.raises(ValidationError):
        list_audit_logs(
            audit_db,
            organization_id="org-1",
            user_id="owner-1",
            since=datetime.now(timezone.utc),
            until=datetime.now(timezone.utc) - timedelta(days=1),
        )


def test_audit_event_rolls_back_with_its_transaction(audit_db):
    record_audit_event(
        audit_db,
        organization_id="org-1",
        user_id="owner-1",
        action="UNCOMMITTED_ACTION",
        resource_type="project",
        resource_id="project-new",
    )
    audit_db.rollback()

    assert (
        audit_db.query(AuditLog)
        .filter(AuditLog.action == "UNCOMMITTED_ACTION")
        .count()
        == 0
    )


def test_audit_event_sanitizes_sensitive_metadata(audit_db):
    event = record_audit_event(
        audit_db,
        organization_id="org-1",
        user_id="owner-1",
        action="PROJECT_UPDATED",
        resource_type="project",
        resource_id="project-sensitive",
        metadata={
            "changed_fields": ["name"],
            "access_token": "abc123",
            "nested": {"authorization": "Bearer abc", "note": "safe"},
            "password": "secret",
            "email": "user@example.com",
            "items": ["ok", {"api_key": "top-secret"}],
        },
    )

    assert event.event_metadata == {
        "changed_fields": ["name"],
        "nested": {"note": "safe"},
        "items": ["ok", {}],
    }


def test_organization_creation_and_deletion_are_audited(audit_db):
    organization = create_organization(
        audit_db,
        user_id="owner-1",
        name="Second Research",
    )
    created_event = (
        audit_db.query(AuditLog)
        .filter(AuditLog.organization_id == organization.id)
        .one()
    )
    assert created_event.action == "ORGANIZATION_CREATED"

    delete_organization(
        audit_db,
        org_id=organization.id,
        user_id="owner-1",
    )
    deletion_event = (
        audit_db.query(AuditLog)
        .filter(
            AuditLog.organization_id == organization.id,
            AuditLog.action == "ORGANIZATION_DELETED",
        )
        .one()
    )
    assert deletion_event.resource_id == organization.id
