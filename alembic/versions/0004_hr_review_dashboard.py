"""HR review dashboard audit trail.

Revision ID: 0004_hr_review
Revises: 0003_excel_intake
Create Date: 2026-06-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_hr_review"
down_revision: str | None = "0003_excel_intake"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hr_review_actions",
        sa.Column("action_id", sa.String(36), nullable=False),
        sa.Column("application_id", sa.String(36), nullable=False),
        sa.Column("validator_result_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.application_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["validator_result_id"], ["validator_results.validator_result_id"]),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("action_id"),
    )
    op.create_index("ix_hr_review_actions_application_id", "hr_review_actions", ["application_id"])
    op.create_index("ix_hr_review_actions_validator_result_id", "hr_review_actions", ["validator_result_id"])
    op.create_index("ix_hr_review_actions_actor_id", "hr_review_actions", ["actor_id"])


def downgrade() -> None:
    op.drop_index("ix_hr_review_actions_actor_id", table_name="hr_review_actions")
    op.drop_index("ix_hr_review_actions_validator_result_id", table_name="hr_review_actions")
    op.drop_index("ix_hr_review_actions_application_id", table_name="hr_review_actions")
    op.drop_table("hr_review_actions")
