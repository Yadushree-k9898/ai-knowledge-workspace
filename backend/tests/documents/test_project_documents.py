from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from app.core.exceptions import PermissionDenied, ResourceNotFound, ValidationError
from app.db.base import Base
from app.db.models import Document, DocumentChunk
from app.db.models.audit_log import AuditLog
from app.db.models.organization import Organization
from app.db.models.organization_member import OrganizationMember, OrgRole
from app.db.models.project import Project
from app.db.models.project_document import ProjectDocument
from app.modules.documents import service as document_service


@pytest.fixture
def documents_db():
    engine = create_engine("sqlite://")
    tables = [
        Organization.__table__,
        OrganizationMember.__table__,
        Project.__table__,
        Document.__table__,
        DocumentChunk.__table__,
        ProjectDocument.__table__,
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
    db.add(
        Project(
            id="project-1",
            organization_id="org-1",
            name="Research project",
            created_by="owner-1",
        )
    )
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine, tables=tables)
        engine.dispose()


def test_upload_project_document_parses_links_and_audits(
    documents_db, monkeypatch
):
    monkeypatch.setattr(
        document_service,
        "generate_embeddings",
        lambda chunks: [[0.0] * 768 for _ in chunks],
    )

    document, chunks_created = document_service.upload_project_document(
        documents_db,
        project_id="project-1",
        user_id="member-1",
        filename="folder\\research.txt",
        file_bytes=b"Research content",
    )

    assert document.filename == "research.txt"
    assert document.content == "Research content"
    assert chunks_created == 1
    assert (
        documents_db.query(ProjectDocument)
        .filter_by(project_id="project-1", document_id=document.id)
        .one()
    )
    assert documents_db.query(DocumentChunk).filter_by(document_id=document.id).count() == 1
    event = (
        documents_db.query(AuditLog)
        .filter_by(action="DOCUMENT_ADDED_TO_PROJECT")
        .one()
    )
    assert event.resource_id == str(document.id)
    assert event.event_metadata == {"project_id": "project-1"}


def test_list_project_documents_only_returns_project_links(documents_db):
    document = Document(
        user_id="owner-1",
        filename="linked.txt",
        content="linked content",
    )
    documents_db.add(document)
    documents_db.flush()
    documents_db.add(
        ProjectDocument(
            project_id="project-1",
            document_id=document.id,
            added_by="owner-1",
        )
    )
    documents_db.commit()

    results = document_service.list_project_documents(
        documents_db,
        project_id="project-1",
        user_id="member-1",
    )

    assert len(results) == 1
    assert results[0][0].filename == "linked.txt"


def test_list_project_documents_denies_non_members(documents_db):
    with pytest.raises(PermissionDenied):
        document_service.list_project_documents(
            documents_db,
            project_id="project-1",
            user_id="outsider",
        )


def test_viewer_cannot_upload_project_documents(documents_db):
    with pytest.raises(PermissionDenied):
        document_service.upload_project_document(
            documents_db,
            project_id="project-1",
            user_id="viewer-1",
            filename="research.txt",
            file_bytes=b"Research content",
        )


def test_remove_document_unlinks_without_deleting_document_or_chunks(documents_db):
    document = Document(
        user_id="owner-1",
        filename="shared.txt",
        content="shared content",
    )
    documents_db.add(document)
    documents_db.flush()
    chunk = DocumentChunk(
        document_id=document.id,
        text_content="shared content",
        embedding=[0.0] * 768,
    )
    documents_db.add(chunk)
    documents_db.add(
        ProjectDocument(
            project_id="project-1",
            document_id=document.id,
            added_by="owner-1",
        )
    )
    documents_db.commit()
    document_id = document.id
    chunk_id = chunk.id

    document_service.remove_document_from_project(
        documents_db,
        project_id="project-1",
        document_id=document_id,
        user_id="owner-1",
    )

    assert documents_db.get(ProjectDocument, ("project-1", document_id)) is None
    assert documents_db.get(Document, document_id) is not None
    assert documents_db.get(DocumentChunk, chunk_id) is not None
    event = (
        documents_db.query(AuditLog)
        .filter_by(action="DOCUMENT_REMOVED_FROM_PROJECT")
        .one()
    )
    assert event.resource_id == str(document_id)


def test_remove_document_not_linked_to_project_returns_not_found(documents_db):
    with pytest.raises(ResourceNotFound):
        document_service.remove_document_from_project(
            documents_db,
            project_id="project-1",
            document_id=999,
            user_id="owner-1",
        )


@pytest.mark.parametrize(
    ("filename", "file_bytes"),
    [("", b"content"), ("unsupported.exe", b"content"), ("empty.txt", b"")],
)
def test_upload_rejects_missing_unsupported_or_empty_files(
    documents_db, monkeypatch, filename, file_bytes
):
    monkeypatch.setattr(
        document_service,
        "generate_embeddings",
        lambda chunks: [[0.0] * 768 for _ in chunks],
    )

    with pytest.raises(ValidationError):
        document_service.upload_project_document(
            documents_db,
            project_id="project-1",
            user_id="owner-1",
            filename=filename,
            file_bytes=file_bytes,
        )
