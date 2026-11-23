"""Add shared analysis rate-limit buckets.

Revision ID: 0003_analysis_abuse_protection
Revises: 0002_finding_uniqueness
Create Date: 2026-11-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_analysis_abuse_protection"
down_revision: str | None = "0002_finding_uniqueness"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_rate_limits",
        sa.Column("bucket_key", sa.String(length=96), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "request_count > 0", name="ck_analysis_rate_limits_request_count_positive"
        ),
        sa.PrimaryKeyConstraint("bucket_key", "window_start"),
    )
    op.create_index(
        "ix_analysis_rate_limits_window_start", "analysis_rate_limits", ["window_start"]
    )


def downgrade() -> None:
    op.drop_index("ix_analysis_rate_limits_window_start", table_name="analysis_rate_limits")
    op.drop_table("analysis_rate_limits")
