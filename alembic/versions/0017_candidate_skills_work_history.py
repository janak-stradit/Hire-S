"""Add skills and work_history JSON columns to candidate_profiles.

Revision ID: 0017_skills_history
Revises: 0016_candidate_intel
Create Date: 2026-06-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_skills_history"
down_revision: str | None = "0016_candidate_intel"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("candidate_profiles", sa.Column("skills",       sa.JSON(), nullable=True))
    op.add_column("candidate_profiles", sa.Column("work_history", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("candidate_profiles", "work_history")
    op.drop_column("candidate_profiles", "skills")
