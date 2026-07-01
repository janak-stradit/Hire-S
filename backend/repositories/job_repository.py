from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.job import Job


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, payload: dict, created_by: str) -> Job:
        job = Job(**payload, created_by=created_by)
        self.session.add(job)
        await self.session.flush()
        return job

    async def get(self, job_id: str) -> Job | None:
        return await self.session.get(Job, job_id)

    async def list(self) -> list[Job]:
        result = await self.session.execute(select(Job).order_by(Job.title.asc()))
        return list(result.scalars().all())

    async def delete(self, job: Job) -> None:
        await self.session.delete(job)

