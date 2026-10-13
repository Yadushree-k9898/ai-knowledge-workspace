"""
Database models package.

Re-exports all models so that:
  - `from app.db.models import Document, DocumentChunk` still works
  - `from app.db.models.profile import Profile` also works
  - `import app.db.models` registers all models with SQLAlchemy Base
"""

# Legacy models (Document, DocumentChunk, User)
from app.db.models_legacy import User, Document, DocumentChunk

# New modular models
from app.db.models.profile import Profile
from app.db.models.organization import Organization
from app.db.models.organization_member import OrganizationMember, OrgRole
from app.db.models.organization_invitation import OrganizationInvitation
from app.db.models.project import Project
from app.db.models.project_document import ProjectDocument
from app.db.models.comparison import ProjectComparison
from app.db.models.research_report import ResearchReport
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.models.notification import Notification
from app.db.models.audit_log import AuditLog

__all__ = [
    "User",
    "Document",
    "DocumentChunk",
    "Profile",
    "Organization",
    "OrganizationMember",
    "OrgRole",
    "OrganizationInvitation",
    "Project",
    "ProjectDocument",
    "ProjectComparison",
    "ResearchReport",
    "Conversation",
    "Message",
    "Notification",
    "AuditLog",
]