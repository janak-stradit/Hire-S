from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class ParsedResume(Base):
    __tablename__ = "parsed_resumes"

    parsed_resume_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    resume_id: Mapped[str] = mapped_column(String(36), ForeignKey("resumes.resume_id"), index=True)
    candidate_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidate_profiles.candidate_id"))
    skills: Mapped[str] = mapped_column(Text, nullable=False, default="")
    total_experience_years: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    education: Mapped[str] = mapped_column(Text, nullable=False, default="")
    certifications: Mapped[str] = mapped_column(Text, nullable=False, default="")
    projects: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sections: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    parsed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    resume = relationship("Resume")


class ParsedJobDescription(Base):
    __tablename__ = "parsed_job_descriptions"

    parsed_jd_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.job_id"), index=True)
    required_skills: Mapped[str] = mapped_column(Text, nullable=False, default="")
    preferred_skills: Mapped[str] = mapped_column(Text, nullable=False, default="")
    experience_min: Mapped[int | None] = mapped_column(Integer)
    experience_max: Mapped[int | None] = mapped_column(Integer)
    education_requirements: Mapped[str] = mapped_column(Text, nullable=False, default="")
    certifications: Mapped[str] = mapped_column(Text, nullable=False, default="")
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    parsed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    job = relationship("Job")


class ValidatorResult(Base):
    __tablename__ = "validator_results"

    validator_result_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("applications.application_id"), index=True
    )
    candidate_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidate_profiles.candidate_id"))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.job_id"))
    intake_batch_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("excel_intake_batches.batch_id"), index=True
    )
    parsed_resume_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("parsed_resumes.parsed_resume_id")
    )
    parsed_jd_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("parsed_job_descriptions.parsed_jd_id")
    )
    skill_score: Mapped[float] = mapped_column(Float, nullable=False)
    experience_score: Mapped[float] = mapped_column(Float, nullable=False)
    education_score: Mapped[float] = mapped_column(Float, nullable=False)
    certification_score: Mapped[float] = mapped_column(Float, nullable=False)
    keyword_score: Mapped[float] = mapped_column(Float, nullable=False)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    queue_target: Mapped[str] = mapped_column(String(80), nullable=False)
    matched_skills: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    missing_skills: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    skill_evidence: Mapped[dict[str, list[str]]] = mapped_column(JSON, nullable=False, default=dict)
    scoring_version: Mapped[str] = mapped_column(String(30), nullable=False, default="2.3")
    validator_version: Mapped[str] = mapped_column(String(40), nullable=False, default="validator-2.3")
    parser_version: Mapped[str] = mapped_column(String(40), nullable=False, default="resume-parser-2.3")
    scoring_config_version: Mapped[str] = mapped_column(String(40), nullable=False, default="scoring-config-2.3")
    decision_policy_version: Mapped[str] = mapped_column(String(40), nullable=False, default="threshold-policy-1.0")
    rejection_reason_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    scoring_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    application = relationship("Application")
    parsed_resume = relationship("ParsedResume")
    parsed_job_description = relationship("ParsedJobDescription")


class ExcelIntakeBatch(Base):
    __tablename__ = "excel_intake_batches"

    batch_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    requirement_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    job_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("jobs.job_id"), index=True)
    candidate_workbook: Mapped[str] = mapped_column(String(1000), nullable=False)
    requirement_workbook: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="RUNNING")
    candidates_read: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidates_imported: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidates_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pass_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fail_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shortlisted_workbook: Mapped[str | None] = mapped_column(String(1000))
    error_report: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
