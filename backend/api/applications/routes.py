from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.database.session import get_session
from backend.models.application import Application
from backend.models.job import Job
from backend.models.user import User
from backend.schemas.application import ApplicationCreate, ApplicationRead
from backend.services.application_service import ApplicationService

router = APIRouter()

_STATUS_NORM: dict[str, str] = {
    "Applied":       "submitted",
    "Under Review":  "under_review",
    "Shortlisted":   "shortlisted",
    "Rejected":      "rejected",
    "Hired":         "hired",
    "Withdrawn":     "withdrawn",
    "withdrawn":     "withdrawn",
    "submitted":     "submitted",
    "under_review":  "under_review",
    "shortlisted":   "shortlisted",
    "rejected":      "rejected",
    "hired":         "hired",
}


class ApplyByRequirementRequest(BaseModel):
    requirement_id: str


@router.post("/apply", response_model=ApplicationRead, status_code=201)
async def apply_to_job(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await ApplicationService(session).apply(current_user, payload.job_id)


@router.post("/apply-by-requirement", status_code=201)
async def apply_by_requirement(
    payload: ApplyByRequirementRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Job).where(Job.requirement_id == payload.requirement_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="No active job found for this requirement. Please ask HR to run the intake process first.")
    app = await ApplicationService(session).apply(current_user, job.job_id)
    return {
        "application_id": app.application_id,
        "job_id": app.job_id,
        "requirement_id": job.requirement_id,
        "role": job.title,
        "department": job.department,
        "status": "submitted",
        "created_at": app.applied_at.isoformat(),
    }


@router.get("/list")
async def list_applications(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if current_user.role != "candidate":
        raise HTTPException(status_code=403, detail="Candidate access required")
    rows = await session.execute(
        select(Application, Job)
        .join(Job, Job.job_id == Application.job_id)
        .where(Application.candidate_id == current_user.id)
        .order_by(Application.applied_at.desc())
    )
    applications = []
    for app, job in rows:
        applications.append({
            "application_id": app.application_id,
            "job_id": app.job_id,
            "requirement_id": job.requirement_id,
            "role": job.title,
            "department": job.department,
            "status": _STATUS_NORM.get(app.application_status, app.application_status.lower()),
            "created_at": app.applied_at.isoformat(),
            "updated_at": app.applied_at.isoformat(),
        })
    return {"applications": applications}


@router.patch("/{application_id}/withdraw")
async def withdraw_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if current_user.role != "candidate":
        raise HTTPException(status_code=403, detail="Candidate access required")
    result = await session.execute(
        select(Application).where(
            Application.application_id == application_id,
            Application.candidate_id == current_user.id,
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.application_status.lower() in ("rejected", "withdrawn", "hired"):
        raise HTTPException(status_code=400, detail="Cannot withdraw application in current state")
    app.application_status = "withdrawn"
    await session.commit()
    return {"status": "withdrawn"}

