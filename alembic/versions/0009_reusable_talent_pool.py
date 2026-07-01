"""Add reusable candidate talent pool and source provenance.

Revision ID: 0009_reusable_talent_pool
Revises: 0008_education_2_3
Create Date: 2026-06-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_reusable_talent_pool"
down_revision: str | None = "0008_education_2_3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "candidate_profiles",
        sa.Column("talent_pool_status", sa.String(40), nullable=False, server_default="AVAILABLE"),
    )
    op.add_column(
        "candidate_profiles",
        sa.Column("reusable_from_pool", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column("candidate_profiles", sa.Column("last_evaluated_at", sa.DateTime(timezone=True)))
    op.add_column("candidate_profiles", sa.Column("last_outcome", sa.String(80)))
    op.execute("UPDATE candidate_profiles SET reusable_from_pool = agent_processing_allowed")
    op.create_index("ix_candidate_profiles_talent_pool_status", "candidate_profiles", ["talent_pool_status"])

    op.create_table(
        "candidate_source_records",
        sa.Column("source_record_id", sa.String(36), primary_key=True),
        sa.Column("candidate_id", sa.String(36), sa.ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("source_reference", sa.String(1000), nullable=False, server_default="unknown"),
        sa.Column("external_profile_id", sa.String(255)),
        sa.Column("source_metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("candidate_id", "source_type", "source_reference", name="uq_candidate_source"),
    )
    op.create_index("ix_candidate_source_records_candidate_id", "candidate_source_records", ["candidate_id"])
    op.create_index("ix_candidate_source_records_external_profile_id", "candidate_source_records", ["external_profile_id"])

    op.create_table(
        "candidate_lifecycle_events",
        sa.Column("event_id", sa.String(36), primary_key=True),
        sa.Column("candidate_id", sa.String(36), sa.ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.application_id", ondelete="SET NULL")),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("from_status", sa.String(40)),
        sa.Column("to_status", sa.String(40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("event_metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_candidate_lifecycle_events_candidate_id", "candidate_lifecycle_events", ["candidate_id"])
    op.create_index("ix_candidate_lifecycle_events_application_id", "candidate_lifecycle_events", ["application_id"])


def downgrade() -> None:
    op.drop_index("ix_candidate_lifecycle_events_application_id", table_name="candidate_lifecycle_events")
    op.drop_index("ix_candidate_lifecycle_events_candidate_id", table_name="candidate_lifecycle_events")
    op.drop_table("candidate_lifecycle_events")
    op.drop_index("ix_candidate_source_records_external_profile_id", table_name="candidate_source_records")
    op.drop_index("ix_candidate_source_records_candidate_id", table_name="candidate_source_records")
    op.drop_table("candidate_source_records")
    op.drop_index("ix_candidate_profiles_talent_pool_status", table_name="candidate_profiles")
    op.drop_column("candidate_profiles", "last_outcome")
    op.drop_column("candidate_profiles", "last_evaluated_at")
    op.drop_column("candidate_profiles", "reusable_from_pool")
    op.drop_column("candidate_profiles", "talent_pool_status")
