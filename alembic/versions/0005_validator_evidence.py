"""Persist explainable validator evidence.

Revision ID: 0005_validator_evidence
Revises: 0004_hr_review
Create Date: 2026-06-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_validator_evidence"
down_revision: str | None = "0004_hr_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "parsed_resumes",
        sa.Column("sections", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "validator_results",
        sa.Column("matched_skills", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "validator_results",
        sa.Column("missing_skills", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "validator_results",
        sa.Column("skill_evidence", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "validator_results",
        sa.Column("scoring_version", sa.String(30), nullable=False, server_default="2.1"),
    )


def downgrade() -> None:
    op.drop_column("validator_results", "scoring_version")
    op.drop_column("validator_results", "skill_evidence")
    op.drop_column("validator_results", "missing_skills")
    op.drop_column("validator_results", "matched_skills")
    op.drop_column("parsed_resumes", "sections")
