"""HR operations API.

The Next.js operations dashboard calls these endpoints after a validator batch
has produced candidate results. Routes here are read/write HR surfaces: summary
cards, candidate lists, evidence detail, pool analytics, reason bank, sourcing
batches, and final HR actions for REVIEW candidates.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.database.session import get_session
from backend.models.candidate import CandidateProfile
from backend.models.user import User
from backend.schemas.admin import (
    CandidateDetail,
    CandidateList,
    DashboardSummary,
    ReviewActionRequest,
    ReviewActionResponse,
)
from backend.schemas.user import UserRead
from backend.services.admin_dashboard_service import AdminDashboardService
from backend.services.security import hash_password

router = APIRouter()


def require_operations_user(current_user: User = Depends(get_current_user)) -> User:
    """Protect HR dashboard endpoints from normal candidate accounts."""
    if current_user.role not in {"recruiter", "hr", "admin"}:
        raise HTTPException(status_code=403, detail="Recruiter, HR, or admin access required")
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


class UserUpdateRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    password: str | None = None


class CreateUserRequest(BaseModel):
    email: str
    role: str = "recruiter"
    password: str


class PoolStatusUpdateRequest(BaseModel):
    talent_pool_status: str


@router.post("/users", response_model=UserRead, status_code=201)
async def create_user(
    payload: CreateUserRequest,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    from backend.services.auth_service import AuthService
    from backend.schemas.user import UserCreate

    if payload.role not in {"candidate", "recruiter", "hr", "admin"}:
        raise HTTPException(status_code=422, detail="Invalid role")
    if len(payload.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    return await AuthService(session).register(
        UserCreate(email=payload.email, password=payload.password, role=payload.role)
    )


@router.get("/users")
async def list_users(
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(User).order_by(User.created_at.desc()))
    users = list(result.scalars().all())
    return {"users": users}


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.role is not None:
        if payload.role not in {"candidate", "recruiter", "hr", "admin"}:
            raise HTTPException(status_code=422, detail="Invalid role")
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        if len(payload.password) < 8:
            raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
        user.password_hash = hash_password(payload.password)
    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    await session.delete(user)
    await session.commit()


class ResetPasswordRequest(BaseModel):
    password: str


@router.post("/users/{user_id}/reset-password", response_model=UserRead)
async def reset_user_password(
    user_id: str,
    payload: ResetPasswordRequest,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if len(payload.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    user.password_hash = hash_password(payload.password)
    await session.commit()
    await session.refresh(user)
    return user


@router.get("/candidates-master")
async def candidates_master(
    search: str | None = Query(default=None, max_length=200),
    talent_pool_status: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    freshness_status: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session),
):
    query = select(CandidateProfile, User).join(User, User.id == CandidateProfile.candidate_id)
    if search:
        term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(User.email).like(term),
                func.lower(CandidateProfile.first_name).like(term),
                func.lower(CandidateProfile.last_name).like(term),
                func.lower(CandidateProfile.first_name + " " + CandidateProfile.last_name).like(
                    term
                ),
                func.lower(CandidateProfile.current_role).like(term),
                func.lower(CandidateProfile.current_company).like(term),
                func.lower(CandidateProfile.city).like(term),
            )
        )
    if talent_pool_status:
        query = query.where(CandidateProfile.talent_pool_status == talent_pool_status)
    if source_type:
        query = query.where(CandidateProfile.source_type == source_type)
    if freshness_status:
        query = query.where(CandidateProfile.profile_freshness_status == freshness_status)

    total_result = await session.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    rows = await session.execute(query.order_by(User.created_at.desc()).limit(limit).offset(offset))
    items = []
    for profile, user in rows:
        items.append(
            {
                "candidate_id": profile.candidate_id,
                "email": user.email,
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "phone": profile.phone,
                "city": profile.city,
                "state": profile.state,
                "country": profile.country,
                "current_company": profile.current_company,
                "current_role": profile.current_role,
                "total_experience": profile.total_experience,
                "expected_salary": profile.expected_salary,
                "notice_period": profile.notice_period,
                "highest_education": profile.highest_education,
                "linkedin_url": profile.linkedin_url,
                "github_url": profile.github_url,
                "portfolio_url": profile.portfolio_url,
                "profile_completion_percentage": profile.profile_completion_percentage,
                "source_type": profile.source_type,
                "verification_status": profile.verification_status,
                "talent_pool_status": profile.talent_pool_status,
                "profile_freshness_status": profile.profile_freshness_status,
                "agent_processing_allowed": profile.agent_processing_allowed,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_evaluated_at": profile.last_evaluated_at.isoformat()
                if profile.last_evaluated_at
                else None,
                "last_outcome": profile.last_outcome,
                "profile_last_refreshed_at": profile.profile_last_refreshed_at.isoformat()
                if profile.profile_last_refreshed_at
                else None,
                "skills": profile.skills or [],
                "work_history": profile.work_history or [],
            }
        )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/summary")
async def summary(
    job_id: str | None = Query(default=None),
    batch_id: str | None = Query(default=None),
    _: User = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session),
):
    from datetime import datetime, timedelta
    from backend.models.application import Application as AppModel
    from backend.models.job import Job as JobModel
    from backend.models.resume import Resume as ResumeModel

    # Aggregate operations metrics for the HR dashboard cards.
    total_candidates = (
        await session.execute(select(func.count()).select_from(CandidateProfile))
    ).scalar_one()
    total_applications = (
        await session.execute(select(func.count()).select_from(AppModel))
    ).scalar_one()
    active_requirements = (
        await session.execute(
            select(func.count()).select_from(JobModel).where(JobModel.status == "open")
        )
    ).scalar_one()
    fresh_candidates = (
        await session.execute(
            select(func.count())
            .select_from(CandidateProfile)
            .where(CandidateProfile.profile_freshness_status == "FRESH")
        )
    ).scalar_one()
    stale_candidates = (
        await session.execute(
            select(func.count())
            .select_from(CandidateProfile)
            .where(CandidateProfile.profile_freshness_status == "STALE")
        )
    ).scalar_one()
    available_pool = (
        await session.execute(
            select(func.count())
            .select_from(CandidateProfile)
            .where(CandidateProfile.talent_pool_status == "AVAILABLE")
        )
    ).scalar_one()
    week_ago = datetime.utcnow() - timedelta(days=7)
    resumes_this_week = (
        await session.execute(
            select(func.count()).select_from(ResumeModel).where(ResumeModel.uploaded_at >= week_ago)
        )
    ).scalar_one()
    # Pending reviews: validator REVIEW decisions without an HR action yet.
    from backend.models.validator import ValidatorResult
    from backend.models.hr_review import HRReviewAction

    review_subq = select(HRReviewAction.application_id)
    pending_reviews = (
        await session.execute(
            select(func.count())
            .select_from(ValidatorResult)
            .where(ValidatorResult.decision == "REVIEW")
            .where(ValidatorResult.application_id.notin_(review_subq))
        )
    ).scalar_one()
    return {
        "total_candidates": total_candidates,
        "total_applications": total_applications,
        "active_requirements": active_requirements,
        "pending_reviews": pending_reviews,
        "fresh_candidates": fresh_candidates,
        "stale_candidates": stale_candidates,
        "available_pool": available_pool,
        "resumes_this_week": resumes_this_week,
    }


@router.get("/pool-analytics")
async def pool_analytics(
    _: User = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session),
):
    # Global pool analytics are intentionally separate from batch metrics so HR
    # does not confuse all-time reusable-pool health with one hiring run.
    return await AdminDashboardService(session).pool_analytics()


@router.get("/reason-bank")
async def reason_bank(
    _: User = Depends(require_operations_user),
):
    # Static reason metadata keeps rejection/review explanations consistent in
    # UI, reports, and downstream agent handoff.
    return AdminDashboardService.reason_bank()


@router.get("/sourcing-batches")
async def sourcing_batches(
    _: User = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session),
):
    # Used by the Batches screen to audit sourcing inputs and validator outputs
    # across multiple job openings.
    return await AdminDashboardService(session).sourcing_batches()


@router.get("/candidates", response_model=CandidateList)
async def candidates(
    job_id: str | None = Query(default=None),
    batch_id: str | None = Query(default=None),
    decision: str | None = Query(default=None, pattern="^(PASS|REVIEW|FAIL)$"),
    hr_action: str | None = Query(default=None, pattern="^(MOVE_FORWARD|HOLD|REJECT)$"),
    workflow_state: str | None = Query(
        default=None, pattern="^(PENDING|MOVE_FORWARD|HOLD|REJECT)$"
    ),
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=100, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session),
):
    # This is the main candidate table endpoint. Filters mirror the dashboard
    # tabs: validator decision, HR action, workflow state, search, and batch.
    return await AdminDashboardService(session).list_candidates(
        job_id, batch_id, decision, hr_action, workflow_state, search, limit, offset
    )


@router.get("/candidates/{application_id}", response_model=CandidateDetail)
async def candidate_detail(
    application_id: str,
    validator_result_id: str | None = Query(default=None),
    _: User = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session),
):
    # Detail view joins parsed resume sections, score evidence, timeline,
    # freshness changes, validator versions, and HR review history.
    return await AdminDashboardService(session).detail(application_id, validator_result_id)


@router.post(
    "/candidates/{application_id}/decision", response_model=ReviewActionResponse, status_code=201
)
async def decide_candidate(
    application_id: str,
    payload: ReviewActionRequest,
    current_user: User = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session),
):
    # HR action is only needed for middle-band REVIEW cases; PASS and FAIL are
    # already auto-routed by validator thresholds.
    return await AdminDashboardService(session).review(application_id, payload, current_user)


_VALID_POOL_STATUSES = {"AVAILABLE", "PLACED", "NOT_LOOKING", "BLACKLISTED"}


@router.patch("/candidates/{candidate_id}/pool-status")
async def update_pool_status(
    candidate_id: str,
    payload: PoolStatusUpdateRequest,
    _: User = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session),
):
    if payload.talent_pool_status not in _VALID_POOL_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid pool status. Must be one of: {', '.join(_VALID_POOL_STATUSES)}",
        )
    result = await session.execute(
        update(CandidateProfile)
        .where(CandidateProfile.candidate_id == candidate_id)
        .values(talent_pool_status=payload.talent_pool_status)
        .returning(CandidateProfile.candidate_id)
    )
    updated = result.scalar_one_or_none()
    if not updated:
        raise HTTPException(status_code=404, detail="Candidate not found")
    await session.commit()
    return {"candidate_id": candidate_id, "talent_pool_status": payload.talent_pool_status}
