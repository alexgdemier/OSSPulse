"""Create normalized repository analysis tables.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

json_type = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("github_id", sa.BigInteger(), nullable=False),
        sa.Column("owner", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("full_name", sa.String(length=201), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("github_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("github_id"),
        sa.UniqueConstraint("full_name"),
    )
    op.create_index("ix_repositories_github_id", "repositories", ["github_id"])
    op.create_index("ix_repositories_full_name", "repositories", ["full_name"])
    op.create_table(
        "analysis_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("health_score", sa.Integer(), nullable=True),
        sa.Column("coverage", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(length=40), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("dimensions", json_type, nullable=False),
        sa.Column("data_completeness", json_type, nullable=False),
        sa.Column("report_data", json_type, nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_reports_analyzed_at", "analysis_reports", ["analyzed_at"])
    op.create_table(
        "dimension_scores",
        sa.Column("report_id", sa.String(length=36), nullable=False),
        sa.Column("dimension", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["analysis_reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("report_id", "dimension"),
    )
    op.create_table(
        "findings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("report_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=12), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("evidence", json_type, nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["analysis_reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_findings_report_id", "findings", ["report_id"])
    op.create_table(
        "insights",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("finding_id", sa.Integer(), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["finding_id"], ["findings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("finding_id"),
    )


def downgrade() -> None:
    op.drop_table("insights")
    op.drop_index("ix_findings_report_id", table_name="findings")
    op.drop_table("findings")
    op.drop_table("dimension_scores")
    op.drop_index("ix_analysis_reports_analyzed_at", table_name="analysis_reports")
    op.drop_table("analysis_reports")
    op.drop_index("ix_repositories_full_name", table_name="repositories")
    op.drop_index("ix_repositories_github_id", table_name="repositories")
    op.drop_table("repositories")
