from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.database.session import get_session
from backend.models.user import User
from backend.schemas.candidate import CandidateProfileRead, CandidateProfileUpdate
from backend.services.candidate_service import CandidateService

router = APIRouter()


def _build_response(profile, user: User) -> dict:
    """Merge CandidateProfile + User into the response shape."""
    return {
        "candidate_id":                profile.candidate_id,
        "email":                       user.email,
        "first_name":                  profile.first_name,
        "last_name":                   profile.last_name,
        "phone":                       profile.phone,
        "city":                        profile.city,
        "state":                       profile.state,
        "country":                     profile.country,
        "current_company":             profile.current_company,
        "current_role":                profile.current_role,
        "total_experience":            profile.total_experience,
        "expected_salary":             profile.expected_salary,
        "notice_period":               profile.notice_period,
        "highest_education":           profile.highest_education,
        "linkedin_url":                profile.linkedin_url,
        "github_url":                  profile.github_url,
        "portfolio_url":               profile.portfolio_url,
        "profile_completion_percentage": profile.profile_completion_percentage,
        "skills":                      profile.skills or [],
        "work_history":                profile.work_history or [],
        "education_history":           profile.education_history or [],
        "source_type":                 profile.source_type,
        "verification_status":         profile.verification_status,
        "talent_pool_status":          profile.talent_pool_status,
        "profile_freshness_status":    profile.profile_freshness_status,
        "member_since":                user.created_at,
        "profile_last_refreshed_at":   profile.profile_last_refreshed_at,
    }


@router.get("/profile", response_model=CandidateProfileRead)
async def get_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    profile = await CandidateService(session).get_profile(current_user)
    return _build_response(profile, current_user)


@router.put("/profile/update", response_model=CandidateProfileRead)
async def update_profile(
    payload: CandidateProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    profile = await CandidateService(session).update_profile(current_user, payload)
    return _build_response(profile, current_user)
