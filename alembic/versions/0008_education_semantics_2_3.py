"""Advance scoring version for semantic education alternatives.

Revision ID: 0008_education_2_3
Revises: 0007_batch_provenance
Create Date: 2026-06-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_education_2_3"
down_revision: str | None = "0007_batch_provenance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "validator_results", "scoring_version", server_default="2.3", existing_type=sa.String(30)
    )


def downgrade() -> None:
    op.alter_column(
        "validator_results", "scoring_version", server_default="2.2", existing_type=sa.String(30)
    )
