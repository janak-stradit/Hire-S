"""Add canonical candidate identity registry.

Revision ID: 0014_candidate_identities
Revises: 0013_backfill_memberships
Create Date: 2026-06-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_candidate_identities"
down_revision: str | None = "0013_backfill_memberships"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "candidate_identities",
        sa.Column("identity_id", sa.String(36), primary_key=True),
        sa.Column(
            "candidate_id",
            sa.String(36),
            sa.ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("identity_type", sa.String(80), nullable=False),
        sa.Column("normalized_value", sa.String(500), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("identity_type", "normalized_value", name="uq_candidate_identity"),
    )
    op.create_index("ix_candidate_identities_candidate_id", "candidate_identities", ["candidate_id"])
    op.execute(
        """
        INSERT INTO candidate_identities (
            identity_id, candidate_id, identity_type, normalized_value,
            source_type, is_primary, created_at, last_seen_at
        )
        SELECT md5('email:' || lower(trim(users.email))), profiles.candidate_id,
               'email', lower(trim(users.email)), profiles.source_type, true, now(), now()
        FROM candidate_profiles profiles
        JOIN users ON users.id = profiles.candidate_id
        ON CONFLICT (identity_type, normalized_value) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index("ix_candidate_identities_candidate_id", table_name="candidate_identities")
    op.drop_table("candidate_identities")
