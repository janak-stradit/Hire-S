"""Phase 2 validator engine schema.

Revision ID: 0002_phase_2
Revises: 0001_phase_1
Create Date: 2026-06-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_phase_2"
down_revision: str | None = "0001_phase_1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "parsed_resumes",
        sa.Column("parsed_resume_id", sa.String(length=36), nullable=False),
        sa.Column("resume_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("skills", sa.Text(), nullable=False),
        sa.Column("total_experience_years", sa.Float(), nullable=False),
        sa.Column("education", sa.Text(), nullable=False),
        sa.Column("certifications", sa.Text(), nullable=False),
        sa.Column("projects", sa.Text(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.candidate_id"]),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"]),
        sa.PrimaryKeyConstraint("parsed_resume_id"),
    )
    op.create_index(op.f("ix_parsed_resumes_resume_id"), "parsed_resumes", ["resume_id"], unique=False)

    op.create_table(
        "parsed_job_descriptions",
        sa.Column("parsed_jd_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("required_skills", sa.Text(), nullable=False),
        sa.Column("preferred_skills", sa.Text(), nullable=False),
        sa.Column("experience_min", sa.Integer(), nullable=True),
        sa.Column("experience_max", sa.Integer(), nullable=True),
        sa.Column("education_requirements", sa.Text(), nullable=False),
        sa.Column("certifications", sa.Text(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.job_id"]),
        sa.PrimaryKeyConstraint("parsed_jd_id"),
    )
    op.create_index(
        op.f("ix_parsed_job_descriptions_job_id"),
        "parsed_job_descriptions",
        ["job_id"],
        unique=False,
    )

    op.create_table(
        "validator_results",
        sa.Column("validator_result_id", sa.String(length=36), nullable=False),
        sa.Column("application_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("parsed_resume_id", sa.String(length=36), nullable=False),
        sa.Column("parsed_jd_id", sa.String(length=36), nullable=False),
        sa.Column("skill_score", sa.Float(), nullable=False),
        sa.Column("experience_score", sa.Float(), nullable=False),
        sa.Column("education_score", sa.Float(), nullable=False),
        sa.Column("certification_score", sa.Float(), nullable=False),
        sa.Column("keyword_score", sa.Float(), nullable=False),
        sa.Column("final_score", sa.Float(), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("queue_target", sa.String(length=80), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.application_id"]),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.candidate_id"]),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.job_id"]),
        sa.ForeignKeyConstraint(["parsed_jd_id"], ["parsed_job_descriptions.parsed_jd_id"]),
        sa.ForeignKeyConstraint(["parsed_resume_id"], ["parsed_resumes.parsed_resume_id"]),
        sa.PrimaryKeyConstraint("validator_result_id"),
    )
    op.create_index(
        op.f("ix_validator_results_application_id"),
        "validator_results",
        ["application_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_validator_results_application_id"), table_name="validator_results")
    op.drop_table("validator_results")
    op.drop_index(op.f("ix_parsed_job_descriptions_job_id"), table_name="parsed_job_descriptions")
    op.drop_table("parsed_job_descriptions")
    op.drop_index(op.f("ix_parsed_resumes_resume_id"), table_name="parsed_resumes")
    op.drop_table("parsed_resumes")
