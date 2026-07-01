from uuid import uuid4

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Job(Base):
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    department: Mapped[str] = mapped_column(String(180), nullable=False)
    location: Mapped[str] = mapped_column(String(180), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(80), nullable=False)
    experience_min: Mapped[int | None] = mapped_column(Integer)
    experience_max: Mapped[int | None] = mapped_column(Integer)
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    skills_required: Mapped[str] = mapped_column(Text, nullable=False)
    preferred_skills: Mapped[str] = mapped_column(Text, nullable=False, default="")
    education_requirements: Mapped[str] = mapped_column(Text, nullable=False, default="")
    mandatory_certifications: Mapped[str] = mapped_column(Text, nullable=False, default="")
    requirement_id: Mapped[str | None] = mapped_column(String(120), unique=True, index=True)
    screening_pass_score: Mapped[float] = mapped_column(Float, nullable=False, default=75)
    screening_review_score: Mapped[float] = mapped_column(Float, nullable=False, default=60)
    intake_source: Mapped[str] = mapped_column(String(40), nullable=False, default="candidate_portal")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="open")
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    creator = relationship("User", back_populates="created_jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
