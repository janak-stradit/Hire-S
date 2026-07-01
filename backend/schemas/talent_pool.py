from typing import Literal

from pydantic import BaseModel, Field


class TalentPoolScreenRequest(BaseModel):
    requirement_id: str = Field(min_length=2, max_length=120)
    max_candidates: int = Field(default=1000, ge=1, le=10000)
    simulation_mode: bool = False


class TalentPoolScreenResponse(BaseModel):
    batch_id: str
    requirement_id: str
    job_id: str
    status: str
    pool_candidates_considered: int
    pool_candidates_evaluated: int
    pass_count: int
    review_count: int
    fail_count: int
    remaining_requested: int


class TalentPoolSummary(BaseModel):
    total: int
    available: int
    screen_ready: int
    simulation_screen_ready: int
    refresh_required: int
    in_process: int
    hired: int
    do_not_contact: int


class CandidateReleaseRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)
    outcome: str = Field(default="DOWNSTREAM_REJECTED", min_length=2, max_length=80)


class StageDecisionRequest(BaseModel):
    stage: Literal["HR_REVIEW", "R1", "T1", "T2", "MANAGERIAL", "FINAL_HR"]
    decision: Literal["ADVANCE", "REJECT", "HOLD", "HIRED"]
    reason: str = Field(min_length=3, max_length=2000)
