"""Align finding uniqueness and repository indexes.

Revision ID: 0002_finding_uniqueness
Revises: 0001_initial
Create Date: 2026-11-23
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_finding_uniqueness"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_repositories_github_id", table_name="repositories")
    op.drop_index("ix_repositories_full_name", table_name="repositories")
    op.create_unique_constraint(
        "uq_finding_report_code_source", "findings", ["report_id", "code", "source_url"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_finding_report_code_source", "findings", type_="unique")
    op.create_index("ix_repositories_full_name", "repositories", ["full_name"])
    op.create_index("ix_repositories_github_id", "repositories", ["github_id"])
