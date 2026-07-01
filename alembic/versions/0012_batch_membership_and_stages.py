"""Add candidate batch membership and downstream stage history.

Revision ID: 0012_batch_membership
Revises: 0011_expand_verification
Create Date: 2026-06-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_batch_membership"
down_revision: str | None = "0011_expand_verification"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "candidate_batch_memberships",
        sa.Column("membership_id", sa.String(36), primary_key=True),
        sa.Column("batch_id", sa.String(36), sa.ForeignKey("excel_intake_batches.batch_id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_id", sa.String(36), sa.ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.application_id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False),
        sa.Column("validator_result_id", sa.String(36), sa.ForeignKey("validator_results.validator_result_id", ondelete="SET NULL")),
        sa.Column("source_kind", sa.String(40), nullable=False),
        sa.Column("validator_decision", sa.String(20), nullable=False),
        sa.Column("final_score", sa.Float(), nullable=False),
        sa.Column("current_stage", sa.String(40), nullable=False, server_default="VALIDATOR"),
        sa.Column("workflow_status", sa.String(60), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("batch_id", "candidate_id", name="uq_batch_candidate"),
    )
    for column in ("batch_id", "candidate_id", "application_id", "job_id", "validator_result_id"):
        op.create_index(f"ix_candidate_batch_memberships_{column}", "candidate_batch_memberships", [column])

    op.create_table(
        "candidate_stage_events",
        sa.Column("stage_event_id", sa.String(36), primary_key=True),
        sa.Column("membership_id", sa.String(36), sa.ForeignKey("candidate_batch_memberships.membership_id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_id", sa.String(36), sa.ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.application_id", ondelete="CASCADE"), nullable=False),
        sa.Column("batch_id", sa.String(36), sa.ForeignKey("excel_intake_batches.batch_id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(40), nullable=False),
        sa.Column("decision", sa.String(40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("membership_id", "candidate_id", "application_id", "batch_id", "actor_id"):
        op.create_index(f"ix_candidate_stage_events_{column}", "candidate_stage_events", [column])


def downgrade() -> None:
    op.drop_table("candidate_stage_events")
    op.drop_table("candidate_batch_memberships")
