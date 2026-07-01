"""Excel intake pipeline and provenance.

Revision ID: 0003_excel_intake
Revises: 0002_phase_2
Create Date: 2026-06-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_excel_intake"
down_revision: str | None = "0002_phase_2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("candidate_profiles", sa.Column("source_type", sa.String(40), nullable=False, server_default="candidate_portal"))
    op.add_column("candidate_profiles", sa.Column("verification_status", sa.String(40), nullable=False, server_default="unverified"))
    op.add_column("candidate_profiles", sa.Column("source_reference", sa.String(1000), nullable=True))
    op.add_column("candidate_profiles", sa.Column("agent_processing_allowed", sa.Boolean(), nullable=False, server_default=sa.true()))

    op.add_column("jobs", sa.Column("preferred_skills", sa.Text(), nullable=False, server_default=""))
    op.add_column("jobs", sa.Column("education_requirements", sa.Text(), nullable=False, server_default=""))
    op.add_column("jobs", sa.Column("mandatory_certifications", sa.Text(), nullable=False, server_default=""))
    op.add_column("jobs", sa.Column("requirement_id", sa.String(120), nullable=True))
    op.add_column("jobs", sa.Column("screening_pass_score", sa.Float(), nullable=False, server_default="75"))
    op.add_column("jobs", sa.Column("screening_review_score", sa.Float(), nullable=False, server_default="60"))
    op.add_column("jobs", sa.Column("intake_source", sa.String(40), nullable=False, server_default="candidate_portal"))
    op.create_index("ix_jobs_requirement_id", "jobs", ["requirement_id"], unique=True)

    op.add_column("applications", sa.Column("intake_source", sa.String(40), nullable=False, server_default="candidate_portal"))
    op.add_column("applications", sa.Column("intake_batch_id", sa.String(36), nullable=True))
    op.create_index("ix_applications_intake_batch_id", "applications", ["intake_batch_id"])

    op.create_table(
        "excel_intake_batches",
        sa.Column("batch_id", sa.String(36), nullable=False),
        sa.Column("requirement_id", sa.String(120), nullable=False),
        sa.Column("job_id", sa.String(36), nullable=True),
        sa.Column("candidate_workbook", sa.String(1000), nullable=False),
        sa.Column("requirement_workbook", sa.String(1000), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("candidates_read", sa.Integer(), nullable=False),
        sa.Column("candidates_imported", sa.Integer(), nullable=False),
        sa.Column("candidates_skipped", sa.Integer(), nullable=False),
        sa.Column("pass_count", sa.Integer(), nullable=False),
        sa.Column("review_count", sa.Integer(), nullable=False),
        sa.Column("fail_count", sa.Integer(), nullable=False),
        sa.Column("shortlisted_workbook", sa.String(1000), nullable=True),
        sa.Column("error_report", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.job_id"]),
        sa.PrimaryKeyConstraint("batch_id"),
    )
    op.create_index("ix_excel_intake_batches_requirement_id", "excel_intake_batches", ["requirement_id"])
    op.create_index("ix_excel_intake_batches_job_id", "excel_intake_batches", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_excel_intake_batches_job_id", table_name="excel_intake_batches")
    op.drop_index("ix_excel_intake_batches_requirement_id", table_name="excel_intake_batches")
    op.drop_table("excel_intake_batches")
    op.drop_index("ix_applications_intake_batch_id", table_name="applications")
    op.drop_column("applications", "intake_batch_id")
    op.drop_column("applications", "intake_source")
    op.drop_index("ix_jobs_requirement_id", table_name="jobs")
    for column in (
        "intake_source", "screening_review_score", "screening_pass_score", "requirement_id",
        "mandatory_certifications", "education_requirements", "preferred_skills",
    ):
        op.drop_column("jobs", column)
    for column in ("agent_processing_allowed", "source_reference", "verification_status", "source_type"):
        op.drop_column("candidate_profiles", column)
