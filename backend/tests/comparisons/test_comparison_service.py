import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import ResourceNotFound, ValidationError
from app.db.base import Base
from app.db.models.audit_log import AuditLog
from app.db.models.audit_log import AuditLog
from app.db.models import Document, Organization, Project
from app.db.models.comparison import ProjectComparison
from app.db.models.project_document import ProjectDocument
from app.modules.comparisons import service


@pytest.fixture
def comparison_db():
    engine = create_engine("sqlite://")
    tables = [
        Organization.__table__,
        Project.__table__,
        Document.__table__,
        ProjectDocument.__table__,
        ProjectComparison.__table__,
        AuditLog.__table__,
    ]
    Base.metadata.create_all(engine, tables=tables)
    session = sessionmaker(bind=engine)()

    organization = Organization(
        id="org-1",
        name="Research",
        slug="research",
        owner_id="owner-1",
    )
    project = Project(
        id="project-1",
        organization_id=organization.id,
        name="Annual reports",
        created_by="owner-1",
    )
    first = Document(user_id="owner-1", filename="2025.pdf", content="Revenue was 100.")
    second = Document(user_id="owner-1", filename="2026.pdf", content="Revenue was 120.")
    session.add_all([organization, project, first, second])
    session.commit()

    try:
        yield session, project, first, second
    finally:
        session.close()
        Base.metadata.drop_all(engine, tables=tables)
        engine.dispose()


def test_attach_documents_and_create_project_comparison(comparison_db):
    db, project, first, second = comparison_db

    service.attach_document(
        db, project=project, document_id=first.id, user_id="owner-1"
    )
    service.attach_document(
        db, project=project, document_id=first.id, user_id="owner-1"
    )
    service.attach_document(
        db, project=project, document_id=second.id, user_id="owner-1"
    )
    comparison = service.create_comparison(
        db,
        project=project,
        user_id="owner-1",
        document_ids=[first.id, second.id],
        instructions="Compare revenue.",
    )

    assert comparison.status == "QUEUED"
    assert service.serialize_comparison(db, comparison)["document_names"] == [
        "2025.pdf",
        "2026.pdf",
    ]
    assert [item["id"] for item in service.list_project_documents(db, project.id)] == [
        second.id,
        first.id,
    ]
    actions = {
        event.action
        for event in db.query(AuditLog)
        .filter(AuditLog.organization_id == project.organization_id)
        .all()
    }
    assert actions == {"DOCUMENT_LINKED_TO_PROJECT", "COMPARISON_CREATED"}


def test_only_document_owner_can_add_document_to_project(comparison_db):
    db, project, first, _ = comparison_db

    with pytest.raises(ResourceNotFound):
        service.attach_document(
            db, project=project, document_id=first.id, user_id="another-user"
        )


def test_comparison_rejects_documents_not_linked_to_project(comparison_db):
    db, project, first, second = comparison_db
    service.attach_document(
        db, project=project, document_id=first.id, user_id="owner-1"
    )

    with pytest.raises(ValidationError):
        service.create_comparison(
            db,
            project=project,
            user_id="owner-1",
            document_ids=[first.id, second.id],
            instructions=None,
        )


def test_comparison_rejects_documents_over_content_limit(comparison_db):
    db, project, first, second = comparison_db
    first.content = "a" * 100_000
    second.content = "b" * 100_001
    db.commit()
    service.attach_document(
        db, project=project, document_id=first.id, user_id="owner-1"
    )
    service.attach_document(
        db, project=project, document_id=second.id, user_id="owner-1"
    )

    with pytest.raises(ValidationError):
        service.create_comparison(
            db,
            project=project,
            user_id="owner-1",
            document_ids=[first.id, second.id],
            instructions=None,
        )
