from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.database.session import get_session
from backend.models.application import Application
from backend.models.job import Job
from backend.models.user import User
from backend.schemas.job import JobCreate, JobRead, JobUpdate
from backend.services.job_service import JobService

router = APIRouter()

_MANAGER_ROLES = {"recruiter", "hr", "admin"}


def _require_manager(user: User) -> None:
    if user.role not in _MANAGER_ROLES:
        raise HTTPException(status_code=403, detail="Job manager role required")


def serialize_job(job: Job) -> JobRead:
    data = {
        "job_id": job.job_id,
        "title": job.title,
        "department": job.department,
        "location": job.location,
        "employment_type": job.employment_type,
        "experience_min": job.experience_min,
        "experience_max": job.experience_max,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "description": job.description,
        "skills_required": [s for s in job.skills_required.split(",") if s.strip()],
        "preferred_skills": [s for s in job.preferred_skills.split(",") if s.strip()],
        "education_requirements": job.education_requirements,
        "mandatory_certifications": [s for s in job.mandatory_certifications.split(",") if s.strip()],
        "status": job.status,
        "created_by": job.created_by,
    }
    return JobRead.model_validate(data)


def _enrich(job: Job, app_count: int) -> dict:
    d = serialize_job(job).model_dump()
    d["requirement_id"] = job.requirement_id
    d["total_applications"] = app_count
    d["screening_pass_score"] = job.screening_pass_score
    d["screening_review_score"] = job.screening_review_score
    return d


@router.post("/create", response_model=JobRead, status_code=201)
async def create_job(
    payload: JobCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    job = await JobService(session).create(current_user, payload)
    return serialize_job(job)


@router.get("/list")
async def list_jobs(
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    query = (
        select(Job, func.count(Application.application_id).label("app_count"))
        .outerjoin(Application, Application.job_id == Job.job_id)
        .group_by(Job.job_id)
    )
    if status_filter:
        query = query.where(Job.status == status_filter)
    if search:
        term = f"%{search.lower()}%"
        query = query.where(
            or_(func.lower(Job.title).like(term), func.lower(Job.department).like(term))
        )
    result = await session.execute(query.order_by(Job.title.asc()))
    jobs = [_enrich(job, app_count) for job, app_count in result]
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/{job_id}/matching-candidates")
async def matching_candidates(
    job_id: str,
    limit: int = Query(default=500, le=500),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return pool candidates ranked by skill match score for this job."""
    _require_manager(current_user)
    job = await JobService(session).get(job_id)
    required_skills = [s.strip().lower() for s in job.skills_required.split(",") if s.strip()]

    from backend.models.candidate import CandidateProfile
    from backend.models.validator import ParsedResume
    from backend.models.application import Application
    from sqlalchemy import or_

    # Fetch reusable candidates with their parsed resumes (latest resume per candidate)
    resume_subq = (
        select(
            ParsedResume.candidate_id,
            func.max(ParsedResume.resume_id).label("latest_resume_id"),
        )
        .group_by(ParsedResume.candidate_id)
        .subquery("latest_resumes")
    )

    stmt = (
        select(CandidateProfile, ParsedResume)
        .join(resume_subq, resume_subq.c.candidate_id == CandidateProfile.candidate_id)
        .join(ParsedResume, ParsedResume.resume_id == resume_subq.c.latest_resume_id)
        .outerjoin(
            Application,
            (Application.candidate_id == CandidateProfile.candidate_id) & (Application.job_id == job_id)
        )
        .where(
            CandidateProfile.reusable_from_pool.is_(True),
            CandidateProfile.agent_processing_allowed.is_(True),
            or_(
                Application.application_id.is_(None),
                CandidateProfile.profile_last_refreshed_at > Application.applied_at
            )
        )
    )
    if job.experience_min is not None:
        stmt = stmt.where(ParsedResume.total_experience_years >= float(job.experience_min))
    if job.experience_max is not None:
        stmt = stmt.where(ParsedResume.total_experience_years <= float(job.experience_max))

    rows = (await session.execute(stmt)).all()

    def _score(resume: ParsedResume) -> tuple[int, list[str], list[str]]:
        resume_text = (resume.skills or "") + " " + (resume.raw_text or "")
        resume_lower = resume_text.lower()
        matched = [s for s in required_skills if s in resume_lower]
        missing = [s for s in required_skills if s not in resume_lower]
        return len(matched), matched, missing

    results = []
    for candidate, resume in rows:
        match_count, matched, missing = _score(resume)
        pct = round(match_count / len(required_skills) * 100) if required_skills else 0
        
        # Quality filter
        if job.screening_review_score and pct < job.screening_review_score:
            continue
            
        decision = "PASS"
        if job.screening_pass_score and pct < job.screening_pass_score:
            decision = "REVIEW"

        results.append({
            "candidate_id":    candidate.candidate_id,
            "name":            f"{candidate.first_name or ''} {candidate.last_name or ''}".strip() or "Unknown",
            "phone":           candidate.phone,
            "city":            candidate.city,
            "state":           candidate.state,
            "freshness":       candidate.profile_freshness_status,
            "experience_years": resume.total_experience_years,
            "matched_skills":  matched,
            "missing_skills":  missing,
            "match_score":     pct,
            "decision":        decision,
            "total_required":  len(required_skills),
        })

    results.sort(key=lambda r: r["match_score"], reverse=True)
    return {
        "job_id":          job_id,
        "job_title":       job.title,
        "total_matches":   len(results),
        "candidates":      results[:limit],
    }

@router.get("/{job_id}/imported-candidates")
async def imported_candidates(
    job_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return candidates who have already been imported for this job."""
    _require_manager(current_user)
    job = await JobService(session).get(job_id)
    required_skills = [s.strip().lower() for s in job.skills_required.split(",") if s.strip()]

    from backend.models.candidate import CandidateProfile
    from backend.models.validator import ParsedResume
    from backend.models.application import Application

    resume_subq = (
        select(
            ParsedResume.candidate_id,
            func.max(ParsedResume.resume_id).label("latest_resume_id"),
        )
        .group_by(ParsedResume.candidate_id)
        .subquery("latest_resumes")
    )

    stmt = (
        select(CandidateProfile, ParsedResume)
        .join(resume_subq, resume_subq.c.candidate_id == CandidateProfile.candidate_id)
        .join(ParsedResume, ParsedResume.resume_id == resume_subq.c.latest_resume_id)
        .join(Application, Application.candidate_id == CandidateProfile.candidate_id)
        .where(Application.job_id == job_id)
    )
    
    rows = (await session.execute(stmt)).all()

    def _score(resume: ParsedResume) -> tuple[int, list[str], list[str]]:
        resume_text = (resume.skills or "") + " " + (resume.raw_text or "")
        resume_lower = resume_text.lower()
        matched = [s for s in required_skills if s in resume_lower]
        missing = [s for s in required_skills if s not in resume_lower]
        return len(matched), matched, missing

    results = []
    for candidate, resume in rows:
        match_count, matched, missing = _score(resume)
        pct = round(match_count / len(required_skills) * 100) if required_skills else 0
        
        decision = "PASS"
        if job.screening_pass_score and pct < job.screening_pass_score:
            decision = "REVIEW"
        if job.screening_review_score and pct < job.screening_review_score:
            decision = "FAIL"

        results.append({
            "candidate_id":    candidate.candidate_id,
            "name":            f"{candidate.first_name or ''} {candidate.last_name or ''}".strip() or "Unknown",
            "phone":           candidate.phone,
            "city":            candidate.city,
            "state":           candidate.state,
            "freshness":       candidate.profile_freshness_status,
            "experience_years": resume.total_experience_years,
            "matched_skills":  matched,
            "missing_skills":  missing,
            "match_score":     pct,
            "decision":        decision,
            "total_required":  len(required_skills),
            "is_imported":     True
        })

    results.sort(key=lambda r: r["match_score"], reverse=True)
    return {
        "job_id":          job_id,
        "job_title":       job.title,
        "total_matches":   len(results),
        "candidates":      results,
    }


class SourceCandidatesRequest(BaseModel):
    limit: int = 500

@router.post("/{job_id}/source-candidates")
async def source_candidates(
    job_id: str,
    payload: SourceCandidatesRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Source top matching pool candidates and create applications/validator results for them."""
    _require_manager(current_user)
    job = await JobService(session).get(job_id)
    required_skills = [s.strip().lower() for s in job.skills_required.split(",") if s.strip()]

    from backend.models.candidate import CandidateProfile
    from backend.models.validator import ParsedResume, ParsedJobDescription, ValidatorResult

    # Fetch latest parsed job description
    parsed_jd = (await session.execute(
        select(ParsedJobDescription)
        .where(ParsedJobDescription.job_id == job_id)
        .order_by(ParsedJobDescription.parsed_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    
    if not parsed_jd:
        # Create a dummy one if it doesn't exist
        parsed_jd = ParsedJobDescription(
            job_id=job_id,
            required_skills=job.skills_required,
            preferred_skills=job.preferred_skills,
            experience_min=job.experience_min,
            experience_max=job.experience_max,
            education_requirements=job.education_requirements or "",
            certifications=job.mandatory_certifications or "",
            raw_text=job.description
        )
        session.add(parsed_jd)
        await session.flush()

    resume_subq = (
        select(
            ParsedResume.candidate_id,
            func.max(ParsedResume.resume_id).label("latest_resume_id"),
        )
        .group_by(ParsedResume.candidate_id)
        .subquery("latest_resumes")
    )
    stmt = (
        select(CandidateProfile, ParsedResume)
        .join(resume_subq, resume_subq.c.candidate_id == CandidateProfile.candidate_id)
        .join(ParsedResume, ParsedResume.resume_id == resume_subq.c.latest_resume_id)
        .where(
            CandidateProfile.reusable_from_pool.is_(True),
            CandidateProfile.agent_processing_allowed.is_(True),
        )
    )
    if job.experience_min is not None:
        stmt = stmt.where(ParsedResume.total_experience_years >= float(job.experience_min))
    if job.experience_max is not None:
        stmt = stmt.where(ParsedResume.total_experience_years <= float(job.experience_max))

    rows = (await session.execute(stmt)).all()

    def _score(resume: ParsedResume) -> tuple[int, list[str], list[str]]:
        resume_text = (resume.skills or "") + " " + (resume.raw_text or "")
        resume_lower = resume_text.lower()
        matched = [s for s in required_skills if s in resume_lower]
        missing = [s for s in required_skills if s not in resume_lower]
        return len(matched), matched, missing

    results = []
    for candidate, resume in rows:
        match_count, matched, missing = _score(resume)
        pct = round(match_count / len(required_skills) * 100) if required_skills else 0
        results.append((candidate, resume, pct, matched, missing))

    results.sort(key=lambda r: r[2], reverse=True)
    top_results = results[:payload.limit]

    imported_count = 0
    for candidate, resume, pct, matched, missing in top_results:
        # Check if application already exists
        existing_app = (await session.execute(
            select(Application).where(
                Application.candidate_id == candidate.candidate_id,
                Application.job_id == job_id
            )
        )).scalar_one_or_none()

        decision = "PASS"
        if job.screening_pass_score and pct < job.screening_pass_score:
            decision = "REVIEW"
        if job.screening_review_score and pct < job.screening_review_score:
            decision = "FAIL"

        app_status = "R1_READY" if decision == "PASS" else "Applied"

        if existing_app:
            app = existing_app
            app.application_status = app_status
        else:
            app = Application(
                candidate_id=candidate.candidate_id,
                job_id=job_id,
                application_status=app_status,
                intake_source="pool_scan"
            )
            session.add(app)
            await session.flush()

        val_result = ValidatorResult(
            application_id=app.application_id,
            candidate_id=candidate.candidate_id,
            job_id=job_id,
            parsed_resume_id=resume.parsed_resume_id,
            parsed_jd_id=parsed_jd.parsed_jd_id,
            skill_score=pct,
            experience_score=100.0,
            education_score=100.0,
            certification_score=100.0,
            keyword_score=pct,
            final_score=pct,
            decision=decision,
            queue_target="manager_review" if decision != "FAIL" else "rejected",
            matched_skills=matched,
            missing_skills=missing,
            explanation=f"Sourced from pool with {pct}% skill match."
        )
        session.add(val_result)
        imported_count += 1

    await session.commit()
    return {"status": "success", "imported": imported_count}


@router.get("/{job_id}")
async def get_job(job_id: str, session: AsyncSession = Depends(get_session)):
    job = await JobService(session).get(job_id)
    result = await session.execute(
        select(func.count(Application.application_id)).where(Application.job_id == job_id)
    )
    app_count = result.scalar_one()
    return _enrich(job, app_count)


@router.put("/{job_id}", response_model=JobRead)
async def update_job(
    job_id: str,
    payload: JobUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    job = await JobService(session).update(current_user, job_id, payload)
    return serialize_job(job)


@router.patch("/{job_id}/status")
async def update_job_status(
    job_id: str,
    payload: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    _require_manager(current_user)
    new_status = payload.get("status")
    if not new_status:
        raise HTTPException(status_code=422, detail="status field required")
    job = await JobService(session).update(current_user, job_id, JobUpdate(status=new_status))
    return {"job_id": job_id, "status": job.status}


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await JobService(session).delete(current_user, job_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/from-excel")
async def jobs_from_excel(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Parse an uploaded Excel/CSV file and upsert Job records into the database."""
    _require_manager(current_user)
    filename = file.filename or ""
    from pathlib import Path
    suffix = Path(filename).suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xlsm"}:
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    from backend.excel_intake.workbooks import _uploaded_requirement_rows, _normalize_requirement_payload, WorkbookValidationError
    from backend.excel_intake.contracts import JobRequirementRow
    try:
        rows = _uploaded_requirement_rows(filename, content)
    except WorkbookValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not rows:
        raise HTTPException(status_code=400, detail="No data rows found in file")

    created = 0
    updated = 0
    errors: list[dict] = []
    used_ids: set[str] = set()

    for idx, row in enumerate(rows, start=2):
        if not any(v not in {None, ""} for v in row.values()):
            continue
        try:
            payload = _normalize_requirement_payload(row, used_ids)
            req = JobRequirementRow.model_validate(payload)
        except Exception as exc:
            errors.append({"row": idx, "error": str(exc)})
            continue

        used_ids.add(req.requirement_id)
        req_status = "open" if req.status.lower() in {"active", "open"} else "draft"

        existing = (await session.execute(
            select(Job).where(Job.requirement_id == req.requirement_id)
        )).scalar_one_or_none()

        if existing:
            existing.title = req.role
            existing.department = req.department
            existing.location = req.location
            existing.employment_type = req.employment_type
            existing.experience_min = req.experience_min
            existing.experience_max = req.experience_max
            existing.salary_min = req.salary_min
            existing.salary_max = req.salary_max
            existing.description = req.jd_text
            existing.skills_required = ", ".join(req.required_skills)
            existing.preferred_skills = ", ".join(req.preferred_skills)
            existing.education_requirements = req.education
            existing.mandatory_certifications = ", ".join(req.mandatory_certifications)
            existing.screening_pass_score = req.screening_pass_score
            existing.screening_review_score = req.screening_review_score
            existing.status = req_status
            updated += 1
        else:
            job = Job(
                job_id=str(uuid4()),
                requirement_id=req.requirement_id,
                title=req.role,
                department=req.department,
                location=req.location,
                employment_type=req.employment_type,
                experience_min=req.experience_min,
                experience_max=req.experience_max,
                salary_min=req.salary_min,
                salary_max=req.salary_max,
                description=req.jd_text,
                skills_required=", ".join(req.required_skills),
                preferred_skills=", ".join(req.preferred_skills),
                education_requirements=req.education,
                mandatory_certifications=", ".join(req.mandatory_certifications),
                screening_pass_score=req.screening_pass_score,
                screening_review_score=req.screening_review_score,
                intake_source="excel_upload",
                status=req_status,
                created_by=current_user.id,
            )
            session.add(job)
            created += 1

    await session.commit()
    return {
        "filename": filename,
        "rows_read": len(rows),
        "created": created,
        "updated": updated,
        "failed": len(errors),
        "errors": errors[:50],
    }
