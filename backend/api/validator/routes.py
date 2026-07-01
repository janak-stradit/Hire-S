"""Validator API for direct application scoring and agent queue reads.

Excel intake uses `ValidatorService` internally, while these endpoints expose
the same scoring engine for direct application evaluation, bulk evaluation,
result lookup, and R1 queue handoff.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_session
from backend.api.dependencies import get_current_user
from backend.models.user import User
from backend.validator.contracts import (
    BulkEvaluateRequest,
    BulkEvaluateResponse,
    EvaluateRequest,
    ValidatorEvaluation,
)
from backend.validator.service import ValidatorService

router = APIRouter()


@router.get("/queues/r1", response_model=list[ValidatorEvaluation])
async def list_r1_queue(
    job_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # R1 agents and HR operators read this queue after PASS candidates are
    # promoted by the pre-screen validator.
    if current_user.role not in {"recruiter", "hr", "admin", "agent"}:
        raise HTTPException(status_code=403, detail="R1 queue access required")
    return await ValidatorService(session).list_queue("R1 Queue", job_id)


@router.post("/evaluate", response_model=ValidatorEvaluation, status_code=201)
async def evaluate_application(
    payload: EvaluateRequest,
    session: AsyncSession = Depends(get_session),
):
    # Direct single-application scoring path used outside the Excel batch flow.
    return await ValidatorService(session).evaluate_application(
        payload.application_id,
        payload.weights,
        payload.thresholds,
    )


@router.get("/result/{validator_result_id}", response_model=ValidatorEvaluation)
async def get_validator_result(
    validator_result_id: str,
    session: AsyncSession = Depends(get_session),
):
    # Fetch immutable score evidence by validator result ID for audit screens.
    return await ValidatorService(session).get_result(validator_result_id)


@router.get("/application/{application_id}", response_model=ValidatorEvaluation)
async def get_application_validator_result(
    application_id: str,
    session: AsyncSession = Depends(get_session),
):
    # Convenience lookup for the latest score tied to one job application.
    return await ValidatorService(session).get_latest_for_application(application_id)


@router.post("/bulk-evaluate", response_model=BulkEvaluateResponse, status_code=201)
async def bulk_evaluate(
    payload: BulkEvaluateRequest,
    session: AsyncSession = Depends(get_session),
):
    # Bulk path keeps the same scoring semantics as single evaluation but lets
    # clients process a selected application list.
    return await ValidatorService(session).bulk_evaluate(
        payload.application_ids,
        payload.weights,
        payload.thresholds,
    )
