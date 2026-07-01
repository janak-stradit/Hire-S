"""Expand candidate verification status for source-qualified labels.

Revision ID: 0011_expand_verification
Revises: 0010_backfill_talent_pool
Create Date: 2026-06-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_expand_verification"
down_revision: str | None = "0010_backfill_talent_pool"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "candidate_profiles",
        "verification_status",
        existing_type=sa.String(40),
        type_=sa.String(80),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "candidate_profiles",
        "verification_status",
        existing_type=sa.String(80),
        type_=sa.String(40),
        existing_nullable=False,
    )
