"""Label pre-evidence validator results as legacy.

Revision ID: 0006_label_legacy
Revises: 0005_validator_evidence
Create Date: 2026-06-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_label_legacy"
down_revision: str | None = "0005_validator_evidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE validator_results SET scoring_version = 'legacy-2.0'")
    op.alter_column(
        "validator_results", "scoring_version", server_default="2.1", existing_type=sa.String(30)
    )


def downgrade() -> None:
    op.execute("UPDATE validator_results SET scoring_version = '2.1'")
