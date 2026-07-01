from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.database.session import get_session
from backend.models.user import User
from backend.schemas.talent_pool import (
    CandidateReleaseRequest,
    TalentPoolScreenRequest,
    TalentPoolScreenResponse,
    TalentPoolSummary,
    StageDecisionRequest,
)
from backend.services.talent_pool_service import TalentPoolService
from backend.services.batch_tracking_service import BatchTrackingService

router = APIRouter()


def require_manager(user: User = Depends(get_current_user)) -> User:
    if user.role not in {"recruiter", "hr", "admin"}:
        raise HTTPException(status_code=403, detail="Recruiter, HR, or admin access required")
    return user


@router.get("/summary", response_model=TalentPoolSummary)
async def summary(
    _: User = Depends(require_manager), session: AsyncSession = Depends(get_session)
):
    return await TalentPoolService(session).summary()


@router.post("/screen", response_model=TalentPoolScreenResponse)
async def screen(
    payload: TalentPoolScreenRequest,
    actor: User = Depends(require_manager),
    session: AsyncSession = Depends(get_session),
):
    return await TalentPoolService(session).screen(actor, payload)


@router.post("/candidates/{candidate_id}/release")
async def release(
    candidate_id: str,
    payload: CandidateReleaseRequest,
    _: User = Depends(require_manager),
    session: AsyncSession = Depends(get_session),
):
    return await TalentPoolService(session).release(candidate_id, payload.reason, payload.outcome)


@router.post("/memberships/{membership_id}/stage-decision")
async def stage_decision(
    membership_id: str,
    payload: StageDecisionRequest,
    actor: User = Depends(require_manager),
    session: AsyncSession = Depends(get_session),
):
    return await BatchTrackingService(session).record_stage_decision(
        membership_id, payload.stage, payload.decision, payload.reason, actor
    )


@router.get("/batches/{batch_id}/memberships")
async def batch_memberships(
    batch_id: str,
    _: User = Depends(require_manager),
    session: AsyncSession = Depends(get_session),
):
    return await BatchTrackingService(session).list_memberships(batch_id)
