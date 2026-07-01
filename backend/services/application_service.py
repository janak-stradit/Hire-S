from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.application import Application
from backend.models.user import User
from backend.repositories.application_repository import ApplicationRepository
from backend.repositories.candidate_repository import CandidateRepository
from backend.repositories.job_repository import JobRepository


class ApplicationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.applications = ApplicationRepository(session)
        self.jobs = JobRepository(session)
        self.candidates = CandidateRepository(session)

    async def apply(self, user: User, job_id: str) -> Application:
        if user.role != "candidate":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Candidate role required")
        if not await self.candidates.get(user.id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile missing")
        if not await self.jobs.get(job_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        existing = await self.applications.get_for_candidate_job(user.id, job_id)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already applied to this job")
        application = await self.applications.create(candidate_id=user.id, job_id=job_id)
        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def list_for_candidate(self, user: User) -> list[Application]:
        if user.role != "candidate":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Candidate role required")
        return await self.applications.list_for_candidate(user.id)

