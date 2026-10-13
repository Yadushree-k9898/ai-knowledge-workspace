import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import AccountDeletionBlocked, ExternalServiceError
from app.db.base import Base
from app.db.models.audit_log import AuditLog
from app.db.models.notification import Notification
from app.db.models.organization import Organization
from app.db.models.organization_member import OrganizationMember, OrgRole
from app.db.models.project import Project
from app.db.models.project_document import ProjectDocument
from app.db.models.profile import Profile
from app.db.models_legacy import Document, DocumentChunk
from app.modules.auth import service as auth_service


@pytest.fixture
def account_db():
    tables = [
        Organization.__table__,
        OrganizationMember.__table__,
        Project.__table__,
        Document.__table__,
        DocumentChunk.__table__,
        ProjectDocument.__table__,
        Profile.__table__,
        Notification.__table__,
        AuditLog.__table__,
    ]
    engine = create_engine("sqlite://")
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
    db.add(
        OrganizationMember(
            id="member-1",
            organization_id="org-1",
            user_id="user-1",
            role=OrgRole.MEMBER,
        )
    )
    db.add(Profile(id="user-1", display_name="Researcher"))
    db.add(
        Document(
            id=1,
            user_id="user-1",
            filename="private.pdf",
            content="private content",
        )
    )
    db.add(
        DocumentChunk(
            id=1,
            document_id=1,
            text_content="private chunk",
        )
    )
    db.add_all(
        [
            Notification(
                id="notification-user",
                user_id="user-1",
                type="GENERAL",
                title="Personal",
                message="For user",
            ),
            Notification(
                id="notification-email",
                user_id=None,
                recipient_email="user@example.com",
                type="INVITATION_RECEIVED",
                title="Invitation",
                message="For email",
            ),
            AuditLog(
                id="audit-1",
                organization_id="org-1",
                user_id="user-1",
                action="PROJECT_CREATED",
                resource_type="project",
                resource_id="project-1",
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


def test_account_deletion_blocks_users_who_own_organizations(
    account_db,
    monkeypatch,
):
    account_db.query(Organization).filter_by(id="org-1").update(
        {Organization.owner_id: "user-1"}
    )
    account_db.commit()
    monkeypatch.setattr(
        auth_service,
        "delete_supabase_identity",
        lambda user_id: pytest.fail("Identity must not be deleted when blocked."),
    )

    with pytest.raises(AccountDeletionBlocked, match="Transfer ownership"):
        auth_service.delete_account(
            account_db,
            user_id="user-1",
            email="user@example.com",
        )


def test_account_deletion_blocks_documents_linked_to_projects(
    account_db,
    monkeypatch,
):
    account_db.add(
        Project(
            id="project-1",
            organization_id="org-1",
            name="Shared project",
            created_by="owner-1",
        )
    )
    account_db.flush()
    account_db.add(
        ProjectDocument(
            project_id="project-1",
            document_id=1,
            added_by="user-1",
        )
    )
    account_db.commit()
    monkeypatch.setattr(
        auth_service,
        "delete_supabase_identity",
        lambda user_id: pytest.fail("Identity must not be deleted when blocked."),
    )

    with pytest.raises(AccountDeletionBlocked, match="project documents"):
        auth_service.delete_account(
            account_db,
            user_id="user-1",
            email="user@example.com",
        )


def test_account_deletion_removes_personal_data_and_preserves_audit_history(
    account_db,
    monkeypatch,
):
    deleted_identities = []
    monkeypatch.setattr(
        auth_service,
        "delete_supabase_identity",
        deleted_identities.append,
    )

    auth_service.delete_account(
        account_db,
        user_id="user-1",
        email="USER@example.com",
    )

    assert deleted_identities == ["user-1"]
    assert account_db.query(Profile).filter_by(id="user-1").count() == 0
    assert account_db.query(Document).filter_by(user_id="user-1").count() == 0
    assert account_db.query(DocumentChunk).filter_by(document_id=1).count() == 0
    assert account_db.query(OrganizationMember).filter_by(user_id="user-1").count() == 0
    assert account_db.query(Notification).count() == 0
    audit_event = account_db.query(AuditLog).filter_by(id="audit-1").one()
    assert audit_event.user_id == "user-1"
    membership_event = (
        account_db.query(AuditLog)
        .filter_by(action="MEMBER_REMOVED", resource_id="member-1")
        .one()
    )
    assert membership_event.user_id == "user-1"
    assert membership_event.event_metadata == {"reason": "ACCOUNT_DELETED"}


def test_identity_provider_failure_rolls_back_application_data(
    account_db,
    monkeypatch,
):
    def fail_delete(_user_id):
        raise ExternalServiceError("Identity provider unavailable.")

    monkeypatch.setattr(auth_service, "delete_supabase_identity", fail_delete)

    with pytest.raises(ExternalServiceError, match="Identity provider unavailable"):
        auth_service.delete_account(
            account_db,
            user_id="user-1",
            email="user@example.com",
        )

    assert account_db.query(Profile).filter_by(id="user-1").count() == 1
    assert account_db.query(Document).filter_by(user_id="user-1").count() == 1
    assert account_db.query(DocumentChunk).filter_by(document_id=1).count() == 1
    assert account_db.query(OrganizationMember).filter_by(user_id="user-1").count() == 1
