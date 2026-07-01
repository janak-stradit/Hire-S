from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CandidateProfileBase(BaseModel):
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    current_company: str | None = Field(default=None, max_length=180)
    current_role: str | None = Field(default=None, max_length=180)
    total_experience: float | None = Field(default=None, ge=0)
    expected_salary: int | None = Field(default=None, ge=0)
    notice_period: str | None = Field(default=None, max_length=80)
    highest_education: str | None = Field(default=None, max_length=180)
    linkedin_url: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=500)
    portfolio_url: str | None = Field(default=None, max_length=500)


class CandidateProfileUpdate(CandidateProfileBase):
    skills: list[str] | None = None
    work_history: list[dict] | None = None
    education_history: list[dict] | None = None


class CandidateProfileRead(CandidateProfileBase):
    candidate_id: str
    email: str | None = None
    profile_completion_percentage: int
    skills: list[str] = []
    work_history: list[dict] = []
    education_history: list[dict] = []
    source_type: str = "candidate_portal"
    verification_status: str = "unverified"
    talent_pool_status: str = "AVAILABLE"
    profile_freshness_status: str = "FRESH"
    member_since: datetime | None = None
    profile_last_refreshed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

