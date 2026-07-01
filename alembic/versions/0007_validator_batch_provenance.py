"""Add validator batch provenance and scoring version 2.2.

Revision ID: 0007_batch_provenance
Revises: 0006_label_legacy
Create Date: 2026-06-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_batch_provenance"
down_revision: str | None = "0006_label_legacy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "validator_results", sa.Column("intake_batch_id", sa.String(36), nullable=True)
    )
    op.create_foreign_key(
        "fk_validator_results_intake_batch",
        "validator_results",
        "excel_intake_batches",
        ["intake_batch_id"],
        ["batch_id"],
    )
    op.create_index(
        "ix_validator_results_intake_batch_id",
        "validator_results",
        ["intake_batch_id"],
    )
    op.alter_column(
        "validator_results", "scoring_version", server_default="2.2", existing_type=sa.String(30)
    )


def downgrade() -> None:
    op.alter_column(
        "validator_results", "scoring_version", server_default="2.1", existing_type=sa.String(30)
    )
    op.drop_index("ix_validator_results_intake_batch_id", table_name="validator_results")
    op.drop_constraint(
        "fk_validator_results_intake_batch", "validator_results", type_="foreignkey"
    )
    op.drop_column("validator_results", "intake_batch_id")
