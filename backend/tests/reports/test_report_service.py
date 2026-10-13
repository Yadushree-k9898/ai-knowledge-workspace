import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import PermissionDenied, ResourceNotFound, ValidationError
from app.db.base import Base
from app.db.models.audit_log import AuditLog
from app.db.models import Document, Organization, OrganizationMember, Project
from app.db.models.organization_member import OrgRole
from app.db.models.project_document import ProjectDocument
from app.db.models.research_report import ResearchReport
from app.modules.reports import service
from app.modules.reports.schemas import ReportType


@pytest.fixture
def report_db():
    engine = create_engine("sqlite://")
    tables = [
        Organization.__table__,
        OrganizationMember.__table__,
        Project.__table__,
        Document.__table__,
        ProjectDocument.__table__,
        ResearchReport.__table__,
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
        name="Market research",
        created_by="owner-1",
    )
    document = Document(
        user_id="owner-1",
        filename="market.pdf",
        content="The market grew by 10 percent.",
    )
    session.add_all([organization, project, document])
    session.flush()
    session.add(
        OrganizationMember(
            id="member-1",
            organization_id=organization.id,
            user_id="owner-1",
            role=OrgRole.OWNER,
        )
    )
    session.add(
        OrganizationMember(
            id="viewer-1",
            organization_id=organization.id,
            user_id="viewer-1",
            role=OrgRole.VIEWER,
        )
    )
    session.add(
        ProjectDocument(
            project_id=project.id,
            document_id=document.id,
            added_by="owner-1",
        )
    )
    session.commit()

    try:
        yield session, project, document
    finally:
        session.close()
        Base.metadata.drop_all(engine, tables=tables)
        engine.dispose()


def test_create_report_uses_documents_linked_to_project(report_db):
    db, project, document = report_db

    report = service.create_report(
        db,
        project_id=project.id,
        user_id="owner-1",
        title="Market summary",
        report_type=ReportType.SUMMARY,
        instructions="Focus on growth.",
    )

    assert report.status == "QUEUED"
    assert report.title == "Market summary"
    assert report.instructions == "Focus on growth."
    assert report.source_document_ids == [document.id]
    assert service.list_project_reports(db, project.id) == [report]


def test_create_report_requires_linked_project_documents(report_db):
    db, project, _ = report_db
    db.query(ProjectDocument).delete()
    db.commit()

    with pytest.raises(ValidationError):
        service.create_report(
            db,
            project_id=project.id,
            user_id="owner-1",
            title="Market summary",
            report_type=ReportType.SUMMARY,
            instructions=None,
        )


def test_report_access_is_project_member_scoped(report_db):
    db, project, _ = report_db

    assert service.get_project_report_access(db, project.id, "owner-1") == project
    with pytest.raises(PermissionDenied):
        service.get_project_report_access(db, project.id, "outsider")
    with pytest.raises(PermissionDenied):
        service.get_project_report_access(db, project.id, "viewer-1", require_write=True)
    with pytest.raises(ResourceNotFound):
        service.get_project_report_access(db, "missing-project", "owner-1")


def test_regenerate_resets_completed_report(report_db):
    db, project, _ = report_db
    report = service.create_report(
        db,
        project_id=project.id,
        user_id="owner-1",
        title="Market summary",
        report_type=ReportType.SUMMARY,
        instructions=None,
    )
    report.status = "READY"
    report.content = "Old output"
    db.commit()

    updated = service.regenerate_report(db, report)

    assert updated.status == "QUEUED"
    assert updated.content is None
    assert updated.error is None


def test_creator_only_can_delete_report(report_db):
    db, project, _ = report_db
    report = service.create_report(
        db,
        project_id=project.id,
        user_id="owner-1",
        title="Market summary",
        report_type=ReportType.SUMMARY,
        instructions=None,
    )

    with pytest.raises(PermissionDenied):
        service.delete_report(db, report, "another-member")

    service.delete_report(db, report, "owner-1")
    with pytest.raises(ResourceNotFound):
        service.get_report(db, report.id)
