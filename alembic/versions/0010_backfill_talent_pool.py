"""Backfill talent-pool state and candidate source provenance.

Revision ID: 0010_backfill_talent_pool
Revises: 0009_reusable_talent_pool
Create Date: 2026-06-22
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0010_backfill_talent_pool"
down_revision: str | None = "0009_reusable_talent_pool"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        WITH latest_valid_result AS (
            SELECT DISTINCT ON (vr.candidate_id)
                vr.candidate_id, vr.decision, vr.evaluated_at
            FROM validator_results vr
            LEFT JOIN excel_intake_batches batch ON batch.batch_id = vr.intake_batch_id
            WHERE vr.intake_batch_id IS NULL OR batch.status = 'COMPLETED'
            ORDER BY vr.candidate_id, vr.evaluated_at DESC
        )
        UPDATE candidate_profiles profile
        SET
            talent_pool_status = CASE
                WHEN latest.decision IN ('PASS', 'REVIEW') THEN 'IN_PROCESS'
                ELSE 'AVAILABLE'
            END,
            reusable_from_pool = CASE
                WHEN profile.agent_processing_allowed = false THEN false
                WHEN latest.decision IN ('PASS', 'REVIEW') THEN false
                ELSE true
            END,
            last_evaluated_at = latest.evaluated_at,
            last_outcome = 'VALIDATOR_' || latest.decision
        FROM latest_valid_result latest
        WHERE profile.candidate_id = latest.candidate_id
        """
    )
    op.execute(
        """
        INSERT INTO candidate_source_records (
            source_record_id, candidate_id, source_type, source_reference,
            source_metadata, first_seen_at, last_seen_at
        )
        SELECT
            md5(profile.candidate_id || profile.source_type || coalesce(profile.source_reference, 'unknown')),
            profile.candidate_id,
            profile.source_type,
            coalesce(profile.source_reference, 'unknown'),
            json_build_object('verification_status', profile.verification_status),
            now(),
            now()
        FROM candidate_profiles profile
        ON CONFLICT (candidate_id, source_type, source_reference) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM candidate_source_records")
    op.execute(
        """
        UPDATE candidate_profiles
        SET talent_pool_status = 'AVAILABLE',
            reusable_from_pool = agent_processing_allowed,
            last_evaluated_at = NULL,
            last_outcome = NULL
        """
    )
