from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    first_name: Mapped[str | None] = mapped_column(String(120))
    last_name: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(40))
    city: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(120))
    current_company: Mapped[str | None] = mapped_column(String(180))
    current_role: Mapped[str | None] = mapped_column(String(180))
    total_experience: Mapped[float | None] = mapped_column(Float)
    expected_salary: Mapped[int | None] = mapped_column(Integer)
    notice_period: Mapped[str | None] = mapped_column(String(80))
    highest_education: Mapped[str | None] = mapped_column(String(180))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    portfolio_url: Mapped[str | None] = mapped_column(String(500))
    profile_completion_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, default="candidate_portal")
    verification_status: Mapped[str] = mapped_column(String(80), nullable=False, default="unverified")
    source_reference: Mapped[str | None] = mapped_column(String(1000))
    agent_processing_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    talent_pool_status: Mapped[str] = mapped_column(
        String(40), nullable=False, default="AVAILABLE", index=True
    )
    reusable_from_pool: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    profile_last_refreshed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    profile_refresh_due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC) + timedelta(days=30),
        nullable=False,
        index=True,
    )
    profile_freshness_status: Mapped[str] = mapped_column(
        String(40), nullable=False, default="FRESH", index=True
    )
    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_outcome: Mapped[str | None] = mapped_column(String(80))
    skills: Mapped[list | None] = mapped_column(JSON, nullable=True)
    work_history: Mapped[list | None] = mapped_column(JSON, nullable=True)
    education_history: Mapped[list | None] = mapped_column(JSON, nullable=True)

    user = relationship("User", back_populates="candidate_profile")
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    source_records = relationship("CandidateSourceRecord", cascade="all, delete-orphan")
    lifecycle_events = relationship("CandidateLifecycleEvent", cascade="all, delete-orphan")


class CandidateSourceRecord(Base):
    __tablename__ = "candidate_source_records"
    __table_args__ = (
        UniqueConstraint("candidate_id", "source_type", "source_reference", name="uq_candidate_source"),
    )

    source_record_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(1000), nullable=False, default="unknown")
    external_profile_id: Mapped[str | None] = mapped_column(String(255), index=True)
    source_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class SourcingBatch(Base):
    __tablename__ = "sourcing_batches"

    sourcing_batch_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    source_reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_label: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="IMPORTED")
    total_candidates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    known_candidates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_candidates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    refreshed_candidates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )


class CandidateRefreshChange(Base):
    __tablename__ = "candidate_refresh_changes"

    refresh_change_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), index=True
    )
    source_record_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("candidate_source_records.source_record_id", ondelete="SET NULL"), index=True
    )
    sourcing_batch_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sourcing_batches.sourcing_batch_id", ondelete="SET NULL"), index=True
    )
    changed_fields: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    old_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    new_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    change_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )


class CandidateIdentity(Base):
    __tablename__ = "candidate_identities"
    __table_args__ = (
        UniqueConstraint("identity_type", "normalized_value", name="uq_candidate_identity"),
    )

    identity_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), index=True
    )
    identity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class CandidateLifecycleEvent(Base):
    __tablename__ = "candidate_lifecycle_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), index=True
    )
    application_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("applications.application_id", ondelete="SET NULL"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(40))
    to_status: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    event_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class CandidateBatchMembership(Base):
    __tablename__ = "candidate_batch_memberships"
    __table_args__ = (
        UniqueConstraint("batch_id", "candidate_id", name="uq_batch_candidate"),
    )

    membership_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    batch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("excel_intake_batches.batch_id", ondelete="CASCADE"), index=True
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), index=True
    )
    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("applications.application_id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.job_id", ondelete="CASCADE"), index=True
    )
    validator_result_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("validator_results.validator_result_id", ondelete="SET NULL"), index=True
    )
    source_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    validator_decision: Mapped[str] = mapped_column(String(20), nullable=False)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    current_stage: Mapped[str] = mapped_column(String(40), nullable=False, default="VALIDATOR")
    workflow_status: Mapped[str] = mapped_column(String(60), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class CandidateStageEvent(Base):
    __tablename__ = "candidate_stage_events"

    stage_event_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    membership_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_batch_memberships.membership_id", ondelete="CASCADE"), index=True
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), index=True
    )
    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("applications.application_id", ondelete="CASCADE"), index=True
    )
    batch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("excel_intake_batches.batch_id", ondelete="CASCADE"), index=True
    )
    stage: Mapped[str] = mapped_column(String(40), nullable=False)
    decision: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
