from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.job import Job
from backend.models.user import User
from backend.repositories.job_repository import JobRepository
from backend.schemas.job import JobCreate, JobUpdate

JOB_MANAGER_ROLES = {"recruiter", "hr", "admin"}


class JobService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.jobs = JobRepository(session)

    async def create(self, user: User, payload: JobCreate) -> Job:
        self._ensure_job_manager(user)
        data = payload.model_dump()
        data["skills_required"] = ",".join(data["skills_required"])
        data["preferred_skills"] = ",".join(data["preferred_skills"])
        data["mandatory_certifications"] = ",".join(data["mandatory_certifications"])
        job = await self.jobs.create(payload=data, created_by=user.id)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get(self, job_id: str) -> Job:
        job = await self.jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return job

    async def list(self) -> list[Job]:
        return await self.jobs.list()

    async def update(self, user: User, job_id: str, payload: JobUpdate) -> Job:
        self._ensure_job_manager(user)
        job = await self.get(job_id)
        updates = payload.model_dump(exclude_unset=True)
        if "skills_required" in updates and updates["skills_required"] is not None:
            updates["skills_required"] = ",".join(updates["skills_required"])
        for field in ("preferred_skills", "mandatory_certifications"):
            if field in updates and updates[field] is not None:
                updates[field] = ",".join(updates[field])
        for field, value in updates.items():
            setattr(job, field, value)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def delete(self, user: User, job_id: str) -> None:
        self._ensure_job_manager(user)
        job = await self.get(job_id)
        await self.jobs.delete(job)
        await self.session.commit()

    @staticmethod
    def _ensure_job_manager(user: User) -> None:
        if user.role not in JOB_MANAGER_ROLES:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Job manager role required")
