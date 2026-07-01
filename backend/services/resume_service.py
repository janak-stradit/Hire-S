from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.settings import get_settings
from backend.models.resume import Resume
from backend.models.user import User
from backend.repositories.candidate_repository import CandidateRepository
from backend.repositories.resume_repository import ResumeRepository

ALLOWED_RESUME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


class ResumeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.resumes = ResumeRepository(session)
        self.candidates = CandidateRepository(session)
        self.settings = get_settings()

    async def upload(self, user: User, file: UploadFile) -> Resume:
        if user.role != "candidate":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Candidate role required")
        profile = await self.candidates.get(user.id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile missing")
        extension = self._validate_file_type(file)
        content = await file.read()
        if len(content) > self.settings.max_resume_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
        storage_dir = Path(self.settings.upload_dir)
        storage_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid4()}{extension}"
        storage_path = storage_dir / stored_name
        storage_path.write_bytes(content)
        resume = await self.resumes.create(
            candidate_id=user.id,
            filename=stored_name,
            original_filename=file.filename or stored_name,
            file_size=len(content),
            file_type=file.content_type or "application/octet-stream",
            storage_path=str(storage_path),
        )
        await self.session.commit()
        await self.session.refresh(resume)
        return resume

    async def list_for_candidate(self, user: User) -> list[Resume]:
        if user.role != "candidate":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Candidate role required")
        return await self.resumes.list_for_candidate(user.id)

    @staticmethod
    def _validate_file_type(file: UploadFile) -> str:
        content_type = file.content_type or ""
        suffix = Path(file.filename or "").suffix.lower()
        expected_suffix = ALLOWED_RESUME_TYPES.get(content_type)
        if expected_suffix and suffix == expected_suffix:
            return expected_suffix
        if suffix in {".pdf", ".docx"} and content_type in {"", "application/octet-stream"}:
            return suffix
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX resumes are supported",
        )

