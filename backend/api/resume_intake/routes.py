"""Resume PDF intake — upload one or many PDFs, parse and upsert into DB."""
from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.database.session import get_session
from backend.models.candidate import CandidateProfile
from backend.models.user import User
from backend.repositories.candidate_repository import CandidateRepository
from backend.repositories.user_repository import UserRepository
from backend.resume_parser.extractor import pdf_to_text
from backend.resume_parser.fields import ParsedResume, parse_resume
from backend.services.security import hash_password

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_FILES     = 50


# ── Response models ───────────────────────────────────────────────────────────

class WorkEntryOut(BaseModel):
    role: str
    company: str
    duration: str


class ParsedField(BaseModel):
    first_name: str | None
    last_name: str | None
    email: str | None
    phone: str | None
    city: str | None
    state: str | None
    current_role: str | None
    current_company: str | None
    total_experience: float | None
    expected_salary: int | None
    notice_period: str | None
    highest_education: str | None
    linkedin_url: str | None
    github_url: str | None
    skills: list[str]
    work_history: list[WorkEntryOut]


class UploadResult(BaseModel):
    filename: str
    status: str            # "created" | "updated" | "skipped" | "error"
    message: str
    candidate_id: str | None
    parsed: ParsedField | None


class BulkUploadResponse(BaseModel):
    total: int
    created: int
    updated: int
    skipped: int
    errors: int
    results: list[UploadResult]


# ── Helper: require admin or hr/recruiter ─────────────────────────────────────

def _require_staff(current_user: User) -> User:
    if current_user.role not in ("admin", "hr", "recruiter"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff access required")
    return current_user


# ── Upsert logic ─────────────────────────────────────────────────────────────

async def _find_by_phone(phone: str, session: AsyncSession) -> CandidateProfile | None:
    """Return the profile whose phone matches, or None."""
    if not phone:
        return None
    result = await session.execute(
        select(CandidateProfile).where(CandidateProfile.phone == phone)
    )
    return result.scalar_one_or_none()


async def _upsert_candidate(
    parsed: ParsedResume,
    filename: str,
    session: AsyncSession,
) -> UploadResult:
    user_repo = UserRepository(session)
    cand_repo = CandidateRepository(session)

    # ── 1. Try to find existing record by email (primary key) ────────────────
    user: User | None    = None
    profile: CandidateProfile | None = None
    action = "created"

    if parsed.email:
        user = await user_repo.get_by_email(parsed.email)

    # ── 2. Fallback: match by phone if email lookup missed ───────────────────
    if user is None and parsed.phone:
        phone_profile = await _find_by_phone(parsed.phone, session)
        if phone_profile:
            # Load the owning user via the candidate_id FK
            user    = await session.get(User, phone_profile.candidate_id)
            profile = phone_profile
            action  = "updated"
            # If we parsed a new email, update the user's email only if it's not
            # already taken by another account.
            if parsed.email and user:
                taken = await user_repo.get_by_email(parsed.email)
                if taken is None:
                    user.email = parsed.email.lower()
                    session.add(user)

    # ── 3. Still nothing — require at least email to create ─────────────────
    if user is None:
        if not parsed.email:
            return UploadResult(
                filename=filename, status="skipped",
                message="No email or matching phone number found in resume.",
                candidate_id=None, parsed=_to_field(parsed),
            )
        # Create fresh user + empty profile
        user = await user_repo.create(
            email=parsed.email,
            password_hash=hash_password(secrets.token_urlsafe(16)),
            role="candidate",
        )
        await session.flush()
        profile = await cand_repo.create_empty(user.id)
        await session.flush()

    else:
        action = "updated"
        if profile is None:
            profile = await cand_repo.get(user.id)
        if profile is None:
            profile = await cand_repo.create_empty(user.id)
            await session.flush()

    # Map parsed fields → profile (only overwrite if parsed has a value)
    def _set(attr: str, val: Any) -> None:
        if val is not None:
            setattr(profile, attr, val)

    _set("first_name",        parsed.first_name)
    _set("last_name",         parsed.last_name)
    _set("phone",             parsed.phone)
    _set("city",              parsed.city)
    _set("country",           parsed.country)
    _set("current_role",      parsed.current_role)
    _set("current_company",   parsed.current_company)
    _set("total_experience",  parsed.total_experience)
    _set("expected_salary",   parsed.expected_salary)
    _set("notice_period",     parsed.notice_period)
    _set("highest_education", parsed.highest_education)
    _set("linkedin_url",      parsed.linkedin_url)
    _set("github_url",        parsed.github_url)
    _set("portfolio_url",     parsed.portfolio_url)

    if parsed.skills:
        profile.skills = parsed.skills
    if parsed.work_history:
        profile.work_history = [e.to_dict() for e in parsed.work_history]

    # Source + last-refreshed timestamp
    profile.source_type = "naukri"
    profile.profile_last_refreshed_at = datetime.now(UTC)

    # Profile completion %
    filled = sum(1 for f in (
        parsed.first_name, parsed.last_name, parsed.phone, parsed.city,
        parsed.current_role, parsed.current_company, parsed.total_experience,
        parsed.linkedin_url, parsed.highest_education,
    ) if f is not None)
    profile.profile_completion_percentage = int(filled / 9 * 100)

    session.add(profile)
    await session.commit()
    await session.refresh(profile)

    return UploadResult(
        filename=filename, status=action,
        message=f"Candidate {action}: {parsed.email}",
        candidate_id=user.id,
        parsed=_to_field(parsed),
    )


def _to_field(p: ParsedResume) -> ParsedField:
    return ParsedField(
        first_name=p.first_name, last_name=p.last_name,
        email=p.email, phone=p.phone, city=p.city, state=p.state,
        current_role=p.current_role, current_company=p.current_company,
        total_experience=p.total_experience, expected_salary=p.expected_salary,
        notice_period=p.notice_period, highest_education=p.highest_education,
        linkedin_url=p.linkedin_url, github_url=p.github_url,
        skills=p.skills,
        work_history=[WorkEntryOut(**e.to_dict()) for e in p.work_history],
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=BulkUploadResponse)
async def upload_resumes(
    files: list[UploadFile] = File(..., description="One or more PDF resume files"),
    current_user: User      = Depends(get_current_user),
    session: AsyncSession   = Depends(get_session),
) -> BulkUploadResponse:
    _require_staff(current_user)

    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Max {MAX_FILES} files per request.")

    results: list[UploadResult] = []

    for upload in files:
        fname = upload.filename or "unknown.pdf"
        try:
            raw = await upload.read()
            if len(raw) > MAX_FILE_SIZE:
                results.append(UploadResult(
                    filename=fname, status="error",
                    message="File exceeds 10 MB limit.",
                    candidate_id=None, parsed=None,
                ))
                continue

            if not fname.lower().endswith(".pdf"):
                results.append(UploadResult(
                    filename=fname, status="error",
                    message="Only PDF files are supported.",
                    candidate_id=None, parsed=None,
                ))
                continue

            text   = pdf_to_text(raw)
            parsed = parse_resume(text)
            result = await _upsert_candidate(parsed, fname, session)
            results.append(result)

        except Exception as exc:
            await session.rollback()
            results.append(UploadResult(
                filename=fname, status="error",
                message=f"Parse error: {exc}",
                candidate_id=None, parsed=None,
            ))

    counts = {s: sum(1 for r in results if r.status == s) for s in ("created", "updated", "skipped", "error")}
    return BulkUploadResponse(
        total=len(results),
        created=counts["created"],
        updated=counts["updated"],
        skipped=counts["skipped"],
        errors=counts["error"],
        results=results,
    )


@router.get("/preview")
async def preview_resume(
    file: UploadFile                = File(...),
    current_user: User              = Depends(get_current_user),
) -> ParsedField:
    """Parse a single PDF and return extracted fields WITHOUT saving to DB."""
    _require_staff(current_user)
    raw  = await file.read()
    text = pdf_to_text(raw)
    p    = parse_resume(text)
    return _to_field(p)
