"""Add durable background document processing jobs.

Revision ID: 0002_document_jobs
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_document_jobs"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_by", sa.String(), nullable=False),
        sa.Column("file_data", sa.LargeBinary(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("document_id", name="uq_document_jobs_document_id"),
    )
    op.create_index("ix_document_jobs_project_id", "document_jobs", ["project_id"])
    op.create_index("ix_document_jobs_requested_by", "document_jobs", ["requested_by"])
    op.create_index("ix_document_jobs_status", "document_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_document_jobs_status", table_name="document_jobs")
    op.drop_index("ix_document_jobs_requested_by", table_name="document_jobs")
    op.drop_index("ix_document_jobs_project_id", table_name="document_jobs")
    op.drop_table("document_jobs")
