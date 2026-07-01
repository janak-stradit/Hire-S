from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.resume import Resume


class ResumeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        candidate_id: str,
        filename: str,
        original_filename: str,
        file_size: int,
        file_type: str,
        storage_path: str,
    ) -> Resume:
        resume = Resume(
            candidate_id=candidate_id,
            filename=filename,
            original_filename=original_filename,
            file_size=file_size,
            file_type=file_type,
            storage_path=storage_path,
        )
        self.session.add(resume)
        await self.session.flush()
        return resume

    async def list_for_candidate(self, candidate_id: str) -> list[Resume]:
        result = await self.session.execute(
            select(Resume).where(Resume.candidate_id == candidate_id).order_by(Resume.uploaded_at.desc())
        )
        return list(result.scalars().all())

