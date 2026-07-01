"""Add education_history JSON column to candidate_profiles.

Revision ID: 0018_edu_history
Revises: 0017_skills_history
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018_edu_history"
down_revision: str | None = "0017_skills_history"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("candidate_profiles", sa.Column("education_history", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("candidate_profiles", "education_history")
