from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

HRDecision = Literal["PASS", "REVIEW", "FAIL"]
HRAction = Literal["MOVE_FORWARD", "HOLD", "REJECT"]


class DashboardSummary(BaseModel):
    total: int
    pass_count: int
    review_count: int
    fail_count: int
    moved_forward: int
    held: int
    rejected_by_hr: int


class CandidateRow(BaseModel):
    application_id: str
    validator_result_id: str
    candidate_id: str
    name: str
    email: str
    current_role: str | None
    location: str
    experience_years: float
    job_id: str
    job_title: str
    final_score: float
    validator_decision: HRDecision
    queue_target: str
    application_status: str
    hr_action: HRAction | None
    source_type: str
    verification_status: str
    evaluated_at: datetime


class ScoreBreakdown(BaseModel):
    skills: float
    experience: float
    education: float
    certifications: float
    keywords: float
    final: float


class ReviewHistoryItem(BaseModel):
    action_id: str
    action: HRAction
    reason: str
    reason_codes: list[str] = Field(default_factory=list)
    actor_email: str
    created_at: datetime


class CandidateDetail(CandidateRow):
    phone: str | None
    current_company: str | None
    education: str
    skills: list[str]
    certifications: str
    projects: str
    resume_sections: dict[str, str]
    matched_skills: list[str]
    missing_skills: list[str]
    skill_evidence: dict[str, list[str]]
    resume_text: str
    resume_filename: str | None
    source_reference: str | None
    explanation: str
    scores: ScoreBreakdown
    pass_threshold: float
    review_threshold: float
    education_requirement: str
    required_certifications: list[str]
    candidate_timeline: list[dict] = Field(default_factory=list)
    refresh_changes: list[dict] = Field(default_factory=list)
    validator_versions: dict = Field(default_factory=dict)
    rejection_reason_codes: list[str] = Field(default_factory=list)
    review_history: list[ReviewHistoryItem]


class CandidateList(BaseModel):
    items: list[CandidateRow]
    total: int
    limit: int
    offset: int


class ReviewActionRequest(BaseModel):
    action: HRAction
    reason: str = Field(min_length=3, max_length=2000)
    reason_codes: list[str] = Field(default_factory=list)
    validator_result_id: str | None = None


class ReviewActionResponse(BaseModel):
    action_id: str
    application_id: str
    action: HRAction
    application_status: str
    created_at: datetime
