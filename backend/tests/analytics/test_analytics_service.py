from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import PermissionDenied, ValidationError
from app.db.base import Base
from app.db.models import Document, Organization, OrganizationMember, Project
from app.db.models.comparison import ProjectComparison
from app.db.models.organization_member import OrgRole
from app.db.models.project_document import ProjectDocument
from app.db.models.research_report import ResearchReport
from app.modules.analytics.service import get_organization_analytics


@pytest.fixture
def analytics_db():
    engine = create_engine("sqlite://")
    tables = [
        Organization.__table__,
        OrganizationMember.__table__,
        Project.__table__,
        Document.__table__,
        ProjectDocument.__table__,
        ResearchReport.__table__,
        ProjectComparison.__table__,
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
    now = datetime.now(timezone.utc)
    document = Document(
        user_id="owner-1",
        filename="market.pdf",
        content="Market grew.",
        created_at=now,
    )
    session.add_all([organization, project, document])
    session.flush()
    session.add_all(
        [
            OrganizationMember(
                id="member-1",
                organization_id=organization.id,
                user_id="owner-1",
                role=OrgRole.OWNER,
            ),
            ProjectDocument(
                project_id=project.id,
                document_id=document.id,
                added_by="owner-1",
            ),
            ResearchReport(
                id="report-ready",
                project_id=project.id,
                created_by="analyst-1",
                title="Market brief",
                report_type="SUMMARY",
                source_document_ids=[document.id],
                status="READY",
                created_at=now,
            ),
            ResearchReport(
                id="report-queued",
                project_id=project.id,
                created_by="analyst-2",
                title="Pending brief",
                report_type="SUMMARY",
                source_document_ids=[document.id],
                status="QUEUED",
                created_at=now,
            ),
            ProjectComparison(
                id="comparison-1",
                project_id=project.id,
                created_by="analyst-3",
                document_ids=[document.id],
                status="COMPLETED",
                created_at=now,
            ),
        ]
    )
    session.commit()

    try:
        yield session, organization, now.date()
    finally:
        session.close()
        Base.metadata.drop_all(engine, tables=tables)
        engine.dispose()


def test_organization_analytics_counts_supported_metrics_and_discloses_gaps(analytics_db):
    db, organization, today = analytics_db

    result = get_organization_analytics(
        db,
        organization_id=organization.id,
        user_id="owner-1",
        date_from=today,
        date_to=today,
    )

    assert result["documents_uploaded"] == 1
    assert result["documents_processed"] is None
    assert result["reports_generated"] == 1
    assert result["active_users"] == 4
    assert result["questions_asked"] is None
    assert result["searches"] is None
    assert result["processing_failures"] is None
    assert result["average_response_latency_ms"] is None
    assert result["ai_usage"] is None
    assert "searches" in result["unavailable_metrics"]


def test_organization_analytics_includes_both_date_boundaries(analytics_db):
    db, organization, today = analytics_db
    result = get_organization_analytics(
        db,
        organization_id=organization.id,
        user_id="owner-1",
        date_from=today - timedelta(days=1),
        date_to=today,
    )

    assert result["documents_uploaded"] == 1
    assert result["reports_generated"] == 1


def test_organization_analytics_excludes_activity_outside_range(analytics_db):
    db, organization, today = analytics_db

    result = get_organization_analytics(
        db,
        organization_id=organization.id,
        user_id="owner-1",
        date_from=today - timedelta(days=2),
        date_to=today - timedelta(days=1),
    )

    assert result["documents_uploaded"] == 0
    assert result["reports_generated"] == 0
    assert result["active_users"] == 0


def test_reports_generated_uses_completion_date(analytics_db):
    db, organization, today = analytics_db
    report = db.query(ResearchReport).filter(ResearchReport.id == "report-ready").one()
    report.created_at = datetime.now(timezone.utc) - timedelta(days=5)
    report.updated_at = datetime.now(timezone.utc)
    db.commit()

    result = get_organization_analytics(
        db,
        organization_id=organization.id,
        user_id="owner-1",
        date_from=today,
        date_to=today,
    )

    assert result["reports_generated"] == 1


def test_organization_analytics_rejects_reversed_date_range(analytics_db):
    db, organization, today = analytics_db

    with pytest.raises(ValidationError):
        get_organization_analytics(
            db,
            organization_id=organization.id,
            user_id="owner-1",
            date_from=today,
            date_to=today - timedelta(days=1),
        )


def test_organization_analytics_requires_membership(analytics_db):
    db, organization, today = analytics_db

    with pytest.raises(PermissionDenied):
        get_organization_analytics(
            db,
            organization_id=organization.id,
            user_id="outsider",
            date_from=today,
            date_to=today,
        )
