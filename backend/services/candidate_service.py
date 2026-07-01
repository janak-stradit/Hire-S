from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.candidate import CandidateProfile
from backend.models.user import User
from backend.repositories.candidate_repository import CandidateRepository
from backend.schemas.candidate import CandidateProfileUpdate


PROFILE_COMPLETION_FIELDS = (
    "first_name",
    "last_name",
    "phone",
    "city",
    "current_role",
    "current_company",
    "total_experience",
    "highest_education",
    "linkedin_url",
    "skills",
)


class CandidateService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.candidates = CandidateRepository(session)

    async def get_profile(self, user: User) -> CandidateProfile:
        self._ensure_candidate(user)
        profile = await self.candidates.get(user.id)
        if not profile:
            profile = await self.candidates.create_empty(user.id)
            await self.session.commit()
            await self.session.refresh(profile)
        return profile

    async def update_profile(self, user: User, payload: CandidateProfileUpdate) -> CandidateProfile:
        profile = await self.get_profile(user)
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(profile, field, value)
        profile.profile_completion_percentage = self._calculate_completion(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    @staticmethod
    def _calculate_completion(profile: CandidateProfile) -> int:
        def _has_value(field: str) -> bool:
            val = getattr(profile, field, None)
            if val is None:
                return False
            if isinstance(val, list):
                return len(val) > 0
            return bool(val)

        completed = sum(1 for f in PROFILE_COMPLETION_FIELDS if _has_value(f))
        return round((completed / len(PROFILE_COMPLETION_FIELDS)) * 100)

    @staticmethod
    def _ensure_candidate(user: User) -> None:
        if user.role != "candidate":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Candidate role required")

