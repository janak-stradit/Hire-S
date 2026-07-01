from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.candidate import CandidateProfile


class CandidateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, candidate_id: str) -> CandidateProfile | None:
        return await self.session.get(CandidateProfile, candidate_id)

    async def create_empty(self, candidate_id: str) -> CandidateProfile:
        profile = CandidateProfile(candidate_id=candidate_id)
        self.session.add(profile)
        await self.session.flush()
        return profile

