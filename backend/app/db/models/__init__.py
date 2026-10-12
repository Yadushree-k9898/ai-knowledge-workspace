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
]
