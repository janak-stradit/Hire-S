"""Add candidate intelligence audit layer.

Revision ID: 0016_candidate_intel
Revises: 0015_profile_freshness
Create Date: 2026-06-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_candidate_intel"
down_revision: str | None = "0015_profile_freshness"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sourcing_batches",
        sa.Column("sourcing_batch_id", sa.String(36), primary_key=True),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("source_reference", sa.String(1000), nullable=False),
        sa.Column("source_label", sa.String(255), nullable=False, server_default=""),
        sa.Column("status", sa.String(40), nullable=False, server_default="IMPORTED"),
        sa.Column("total_candidates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("known_candidates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_candidates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("refreshed_candidates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sourcing_batches_source_type", "sourcing_batches", ["source_type"])
    op.create_index("ix_sourcing_batches_created_at", "sourcing_batches", ["created_at"])

    op.create_table(
        "candidate_refresh_changes",
        sa.Column("refresh_change_id", sa.String(36), primary_key=True),
        sa.Column(
            "candidate_id",
            sa.String(36),
            sa.ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_record_id",
            sa.String(36),
            sa.ForeignKey("candidate_source_records.source_record_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "sourcing_batch_id",
            sa.String(36),
            sa.ForeignKey("sourcing_batches.sourcing_batch_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("changed_fields", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("old_snapshot", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("new_snapshot", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("change_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_candidate_refresh_changes_candidate_id", "candidate_refresh_changes", ["candidate_id"])
    op.create_index("ix_candidate_refresh_changes_source_record_id", "candidate_refresh_changes", ["source_record_id"])
    op.create_index("ix_candidate_refresh_changes_sourcing_batch_id", "candidate_refresh_changes", ["sourcing_batch_id"])
    op.create_index("ix_candidate_refresh_changes_created_at", "candidate_refresh_changes", ["created_at"])

    op.add_column("validator_results", sa.Column("validator_version", sa.String(40), nullable=False, server_default="validator-2.3"))
    op.add_column("validator_results", sa.Column("parser_version", sa.String(40), nullable=False, server_default="resume-parser-2.3"))
    op.add_column("validator_results", sa.Column("scoring_config_version", sa.String(40), nullable=False, server_default="scoring-config-2.3"))
    op.add_column("validator_results", sa.Column("decision_policy_version", sa.String(40), nullable=False, server_default="threshold-policy-1.0"))
    op.add_column("validator_results", sa.Column("rejection_reason_codes", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("validator_results", sa.Column("scoring_metadata", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("hr_review_actions", sa.Column("reason_codes", sa.JSON(), nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("hr_review_actions", "reason_codes")
    op.drop_column("validator_results", "scoring_metadata")
    op.drop_column("validator_results", "rejection_reason_codes")
    op.drop_column("validator_results", "decision_policy_version")
    op.drop_column("validator_results", "scoring_config_version")
    op.drop_column("validator_results", "parser_version")
    op.drop_column("validator_results", "validator_version")
    op.drop_index("ix_candidate_refresh_changes_created_at", table_name="candidate_refresh_changes")
    op.drop_index("ix_candidate_refresh_changes_sourcing_batch_id", table_name="candidate_refresh_changes")
    op.drop_index("ix_candidate_refresh_changes_source_record_id", table_name="candidate_refresh_changes")
    op.drop_index("ix_candidate_refresh_changes_candidate_id", table_name="candidate_refresh_changes")
    op.drop_table("candidate_refresh_changes")
    op.drop_index("ix_sourcing_batches_created_at", table_name="sourcing_batches")
    op.drop_index("ix_sourcing_batches_source_type", table_name="sourcing_batches")
    op.drop_table("sourcing_batches")
