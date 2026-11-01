"""Initial schema baseline for the workspace.

Revision ID: 0001_initial
Revises:
"""
from alembic import op

from app.db.base import Base
import app.db.models  # noqa: F401 — register every SQLAlchemy model

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pgvector must exist before SQLAlchemy creates the document_chunks table.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    # Drop application tables but leave the shared PostgreSQL extension intact.
    Base.metadata.drop_all(bind=op.get_bind())
