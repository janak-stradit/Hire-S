from pathlib import Path
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class JobRequirementRow(BaseModel):
    requirement_id: str = Field(min_length=2, max_length=120)
    role: str = Field(min_length=2, max_length=180)
    department: str = Field(min_length=2, max_length=180)
    location: str = Field(min_length=2, max_length=180)
    employment_type: str = "Full-time"
    experience_min: int | None = Field(default=None, ge=0)
    experience_max: int | None = Field(default=None, ge=0)
    required_skills: list[str] = Field(min_length=1)
    preferred_skills: list[str] = Field(default_factory=list)
    education: str = ""
    mandatory_certifications: list[str] = Field(default_factory=list)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    work_mode: str = "Hybrid"
    role_title_variants: list[str] = Field(default_factory=list)
    must_have_skills_min_experience: str = ""
    preferred_industry_domain: str = ""
    notice_period_max_days: int | None = Field(default=None, ge=0)
    candidate_freshness_days: int = Field(default=30, ge=1, le=365)
    willing_to_relocate: bool | None = None
    source_priority: list[str] = Field(default_factory=list)
    jd_text: str = Field(min_length=10)
    screening_pass_score: float = Field(default=75, ge=0, le=100)
    screening_review_score: float = Field(default=60, ge=0, le=100)
    status: str = "active"

    @field_validator("experience_max")
    @classmethod
    def experience_range(cls, value, info):
        minimum = info.data.get("experience_min")
        if value is not None and minimum is not None and value < minimum:
            raise ValueError("experience_max must be >= experience_min")
        return value

    @field_validator("salary_max")
    @classmethod
    def salary_range(cls, value, info):
        minimum = info.data.get("salary_min")
        if value is not None and minimum is not None and value < minimum:
            raise ValueError("salary_max must be >= salary_min")
        return value

    @field_validator("screening_review_score")
    @classmethod
    def threshold_range(cls, value, info):
        pass_score = info.data.get("screening_pass_score", 75)
        if value >= pass_score:
            raise ValueError("screening_review_score must be lower than screening_pass_score")
        return value


class CandidateIntakeRow(BaseModel):
    candidate_id: str | None = None
    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    current_company: str | None = None
    current_role: str | None = None
    total_experience: float | None = None
    expected_salary: int | None = None
    notice_period: str | None = None
    preferred_work_mode: str | None = None
    willing_to_relocate: bool | None = None
    preferred_locations: str | None = None
    industry_domain: str | None = None
    profile_last_updated_at: datetime | None = None
    profile_refresh_cycle_days: int | None = Field(default=None, ge=1, le=365)
    highest_education: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    original_filename: str = ""
    storage_path: str = ""
    file_size: int = 0
    file_type: str = "application/octet-stream"
    raw_text: str = Field(min_length=20)
    source_type: str
    verification_status: str
    source_reference: str | None = None
    external_profile_id: str | None = None
    agent_processing_allowed: bool = False


class ExcelIntakeRequest(BaseModel):
    candidate_workbook: Path = Path("storage/candidate_pool/hirex_candidates.xlsx")
    requirement_workbook: Path = Path("storage/job_requirements/jd_input.xlsx")
    include_synthetic: bool = False
    requirement_id: str | None = None
    candidate_pool: str | None = None
    max_candidates: int = Field(default=10000, ge=1, le=100000)


class CandidatePoolSummary(BaseModel):
    pool: str
    label: str
    workbook: str
    total_rows: int
    eligible_rows: int
    simulation_only: bool


class ExcelIntakeConfiguration(BaseModel):
    requirements: list[JobRequirementRow]
    candidate_pools: list[CandidatePoolSummary]


class RequirementUpsertRequest(JobRequirementRow):
    created_by: str = "HR / Talent Lead"


class RequirementStatusRequest(BaseModel):
    status: str = Field(pattern="^(active|draft|inactive|paused|closed)$")


class ExcelIntakeResult(BaseModel):
    batch_id: str
    requirement_id: str
    job_id: str
    status: str
    candidates_read: int
    candidates_imported: int
    candidates_skipped: int
    pass_count: int
    review_count: int
    fail_count: int
    shortlisted_workbook: str
    rejected_workbook: str
