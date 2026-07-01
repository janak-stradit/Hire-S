"""Backfill batch memberships from persisted validator results.

Revision ID: 0013_backfill_memberships
Revises: 0012_batch_membership
Create Date: 2026-06-22
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0013_backfill_memberships"
down_revision: str | None = "0012_batch_membership"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO candidate_batch_memberships (
            membership_id, batch_id, candidate_id, application_id, job_id,
            validator_result_id, source_kind, validator_decision, final_score,
            current_stage, workflow_status, created_at, updated_at
        )
        SELECT
            md5(result.intake_batch_id || result.candidate_id),
            result.intake_batch_id,
            result.candidate_id,
            result.application_id,
            result.job_id,
            result.validator_result_id,
            CASE WHEN profile.source_type = 'synthetic' THEN 'SYNTHETIC' ELSE 'EXTERNAL' END,
            result.decision,
            result.final_score,
            CASE result.decision
                WHEN 'PASS' THEN 'R1'
                WHEN 'REVIEW' THEN 'HR_REVIEW'
                ELSE 'COMPLETE'
            END,
            CASE result.decision
                WHEN 'PASS' THEN 'R1_READY'
                WHEN 'REVIEW' THEN 'HR_REVIEW'
                ELSE 'REJECTED'
            END,
            result.evaluated_at,
            result.evaluated_at
        FROM validator_results result
        JOIN candidate_profiles profile ON profile.candidate_id = result.candidate_id
        JOIN excel_intake_batches batch ON batch.batch_id = result.intake_batch_id
        WHERE result.intake_batch_id IS NOT NULL
          AND batch.status = 'COMPLETED'
        ON CONFLICT (batch_id, candidate_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM candidate_batch_memberships")
