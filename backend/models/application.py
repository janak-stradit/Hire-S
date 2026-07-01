from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job"),)

    application_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_profiles.candidate_id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.job_id"), index=True)
    application_status: Mapped[str] = mapped_column(String(80), nullable=False, default="Applied")
    intake_source: Mapped[str] = mapped_column(String(40), nullable=False, default="candidate_portal")
    intake_batch_id: Mapped[str | None] = mapped_column(String(36), index=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    candidate = relationship("CandidateProfile", back_populates="applications")
    job = relationship("Job", back_populates="applications")
