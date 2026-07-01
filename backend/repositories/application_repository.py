from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.application import Application


class ApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, candidate_id: str, job_id: str) -> Application:
        application = Application(candidate_id=candidate_id, job_id=job_id)
        self.session.add(application)
        await self.session.flush()
        return application

    async def get_for_candidate_job(self, candidate_id: str, job_id: str) -> Application | None:
        result = await self.session.execute(
            select(Application).where(
                Application.candidate_id == candidate_id,
                Application.job_id == job_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_candidate(self, candidate_id: str) -> list[Application]:
        result = await self.session.execute(
            select(Application)
            .where(Application.candidate_id == candidate_id)
            .order_by(Application.applied_at.desc())
        )
        return list(result.scalars().all())

