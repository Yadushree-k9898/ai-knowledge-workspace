from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models.audit_log import AuditLog
from app.db.models import Document, Organization, OrganizationMember, Project
from app.db.models.notification import Notification
from app.db.models.organization_invitation import OrganizationInvitation
from app.db.models.organization_member import OrgRole
from app.db.models.project_document import ProjectDocument
from app.db.models.research_report import ResearchReport
from app.modules.organizations.service import create_invitation
from app.workers.jobs import generate_report as report_worker


def test_invitation_creation_notifies_email_recipient():
    tables = [
        Organization.__table__,
        OrganizationMember.__table__,
        OrganizationInvitation.__table__,
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
            user_id="owner-1",
            role=OrgRole.OWNER,
        )
    )
    db.commit()

    try:
        invitation = create_invitation(
            db,
            org_id="org-1",
            user_id="owner-1",
            email="invitee@example.com",
            role=OrgRole.MEMBER,
        )
        notices = db.query(Notification).all()
        assert len(notices) == 1
        assert notices[0].recipient_email == "invitee@example.com"
        assert notices[0].link == f"/invitations/{invitation.token}"
    finally:
        db.close()
        Base.metadata.drop_all(engine, tables=tables)
        engine.dispose()


def test_report_worker_notifies_creator_on_success(monkeypatch):
    tables = [
        Organization.__table__,
        Project.__table__,
        Document.__table__,
        ProjectDocument.__table__,
        ResearchReport.__table__,
        Notification.__table__,
    ]
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine, tables=tables)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()
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
        content="The market grew.",
    )
    db.add_all([organization, project, document])
    db.flush()
    db.add(
        ProjectDocument(
            project_id=project.id,
            document_id=document.id,
            added_by="owner-1",
        )
    )
    db.add(
        ResearchReport(
            id="report-1",
            project_id=project.id,
            created_by="analyst-1",
            title="Market brief",
            report_type="SUMMARY",
            source_document_ids=[document.id],
            status="QUEUED",
        )
    )
    db.commit()
    db.close()

    class FakeModel:
        def generate_content(self, _prompt):
            return SimpleNamespace(text="Market findings")

    monkeypatch.setattr(report_worker, "SessionLocal", session_factory)
    monkeypatch.setattr(report_worker.genai, "configure", lambda **_kwargs: None)
    monkeypatch.setattr(report_worker.genai, "GenerativeModel", lambda _name: FakeModel())

    try:
        report_worker._process_report("report-1")
        db = session_factory()
        report = db.get(ResearchReport, "report-1")
        notice = db.query(Notification).one()
        assert report.status == "READY"
        assert notice.user_id == "analyst-1"
        assert notice.type == "REPORT_READY"
        db.close()
    finally:
        Base.metadata.drop_all(engine, tables=tables)
        engine.dispose()
