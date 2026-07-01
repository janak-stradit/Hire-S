from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.database.session import get_session
from backend.models.user import User
from backend.schemas.resume import ResumeRead
from backend.services.resume_service import ResumeService

router = APIRouter()


@router.post("/upload", response_model=ResumeRead, status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await ResumeService(session).upload(current_user, file)


@router.get("/list", response_model=list[ResumeRead])
async def list_resumes(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await ResumeService(session).list_for_candidate(current_user)

