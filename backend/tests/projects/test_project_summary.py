from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pytest

from app.core.exceptions import PermissionDenied
from app.db.base import Base
from app.db.models.audit_log import AuditLog
from app.db.models.organization import Organization
from app.db.models.organization_member import OrganizationMember, OrgRole
from app.db.models.project import Project
from app.db.models.project_document import ProjectDocument
from app.db.models.research_report import ResearchReport
from app.db.models_legacy import Document
from app.modules.projects.service import get_project_summary


@pytest.fixture
def project_summary_db():
    tables = [
        Organization.__table__,
        OrganizationMember.__table__,
        Project.__table__,
        Document.__table__,
        ProjectDocument.__table__,
        ResearchReport.__table__,
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
            id="owner-member",
            organization_id="org-1",
            user_id="owner-1",
            role=OrgRole.OWNER,
        )
    )
    db.add_all(
        [
            Project(
                id="project-1",
                organization_id="org-1",
                name="Project One",
                created_by="owner-1",
            ),
            Project(
                id="project-2",
                organization_id="org-1",
                name="Project Two",
                created_by="owner-1",
            ),
            Document(id=1, user_id="owner-1", filename="one.pdf", content="One"),
            Document(id=2, user_id="owner-1", filename="two.pdf", content="Two"),
        ]
    )
    db.flush()
    db.add_all(
        [
            ProjectDocument(
                project_id="project-1",
                document_id=1,
                added_by="owner-1",
            ),
            ProjectDocument(
                project_id="project-1",
                document_id=2,
                added_by="owner-1",
            ),
            ProjectDocument(
                project_id="project-2",
                document_id=2,
                added_by="owner-1",
            ),
            ResearchReport(
                id="report-1",
                project_id="project-1",
                created_by="owner-1",
                title="Report One",
                report_type="SUMMARY",
                source_document_ids=[1, 2],
                status="READY",
            ),
            ResearchReport(
                id="report-2",
                project_id="project-2",
                created_by="owner-1",
                title="Report Two",
                report_type="SUMMARY",
                source_document_ids=[2],
                status="READY",
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


def test_project_summary_counts_only_resources_linked_to_project(project_summary_db):
    summary = get_project_summary(
        project_summary_db,
        project_id="project-1",
        user_id="owner-1",
    )

    assert summary == {
        "project_id": "project-1",
        "name": "Project One",
        "document_count": 2,
        "conversation_count": 0,
        "report_count": 1,
    }


def test_project_summary_requires_organization_membership(project_summary_db):
    with pytest.raises(PermissionDenied):
        get_project_summary(
            project_summary_db,
            project_id="project-1",
            user_id="outsider",
        )
