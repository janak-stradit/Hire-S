"""Add candidate profile freshness tracking.

Revision ID: 0015_profile_freshness
Revises: 0014_candidate_identities
Create Date: 2026-06-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015_profile_freshness"
down_revision: str | None = "0014_candidate_identities"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "candidate_profiles",
        sa.Column(
            "profile_last_refreshed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "candidate_profiles",
        sa.Column(
            "profile_refresh_due_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "candidate_profiles",
        sa.Column(
            "profile_freshness_status",
            sa.String(40),
            nullable=True,
        ),
    )
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            UPDATE candidate_profiles
            SET profile_last_refreshed_at = COALESCE(last_evaluated_at, now()),
                profile_refresh_due_at = COALESCE(last_evaluated_at, now()) + interval '30 days',
                profile_freshness_status = 'FRESH'
            """
        )
        op.alter_column("candidate_profiles", "profile_last_refreshed_at", nullable=False)
        op.alter_column("candidate_profiles", "profile_refresh_due_at", nullable=False)
        op.alter_column("candidate_profiles", "profile_freshness_status", nullable=False)
    elif bind.dialect.name == "sqlite":
        op.execute(
            """
            UPDATE candidate_profiles
            SET profile_last_refreshed_at = COALESCE(last_evaluated_at, CURRENT_TIMESTAMP),
                profile_refresh_due_at = datetime(COALESCE(last_evaluated_at, CURRENT_TIMESTAMP), '+30 days'),
                profile_freshness_status = 'FRESH'
            """
        )
    else:
        op.execute(
            """
            UPDATE candidate_profiles
            SET profile_last_refreshed_at = COALESCE(last_evaluated_at, CURRENT_TIMESTAMP),
                profile_refresh_due_at = COALESCE(last_evaluated_at, CURRENT_TIMESTAMP),
                profile_freshness_status = 'FRESH'
            """
        )
    op.create_index(
        "ix_candidate_profiles_profile_refresh_due_at",
        "candidate_profiles",
        ["profile_refresh_due_at"],
    )
    op.create_index(
        "ix_candidate_profiles_profile_freshness_status",
        "candidate_profiles",
        ["profile_freshness_status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_candidate_profiles_profile_freshness_status",
        table_name="candidate_profiles",
    )
    op.drop_index("ix_candidate_profiles_profile_refresh_due_at", table_name="candidate_profiles")
    op.drop_column("candidate_profiles", "profile_freshness_status")
    op.drop_column("candidate_profiles", "profile_refresh_due_at")
    op.drop_column("candidate_profiles", "profile_last_refreshed_at")
