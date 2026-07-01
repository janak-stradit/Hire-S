"""Restore authorized source provenance without creating applications or validator results."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
import sys
from uuid import uuid4

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.database.session import AsyncSessionLocal
from backend.excel_intake.workbooks import read_candidates
from backend.models.candidate import CandidateProfile, CandidateSourceRecord
from backend.models.user import User
from backend.models.resume import Resume
from backend.models.validator import ParsedResume
from backend.services.security import hash_password
from backend.validator.resume_parser import parse_resume_text


async def main() -> None:
    candidates, skipped = read_candidates(
        ROOT / "storage/candidate_pool/hirex_candidates.xlsx",
        include_synthetic=False,
    )
    updated = 0
    missing = 0
    async with AsyncSessionLocal() as session:
        for candidate in candidates:
            user = await session.scalar(select(User).where(User.email == candidate.email.lower()))
            if not user:
                user = User(
                    id=candidate.candidate_id or str(uuid4()),
                    email=candidate.email.lower(),
                    password_hash=hash_password(str(uuid4())),
                    role="candidate",
                    is_active=True,
                )
                session.add(user)
                await session.flush()
            profile = await session.get(CandidateProfile, user.id)
            if not profile:
                profile = CandidateProfile(
                    candidate_id=user.id,
                    talent_pool_status="AVAILABLE",
                    reusable_from_pool=True,
                )
                session.add(profile)
            for field in (
                "first_name", "last_name", "phone", "city", "state", "country",
                "current_company", "current_role", "total_experience", "expected_salary",
                "notice_period", "highest_education", "linkedin_url", "github_url",
                "portfolio_url",
            ):
                setattr(profile, field, getattr(candidate, field))
            profile.profile_completion_percentage = 100
            profile.agent_processing_allowed = True
            profile.reusable_from_pool = profile.talent_pool_status in {None, "AVAILABLE"}
            profile.source_type = candidate.source_type
            profile.verification_status = candidate.verification_status
            profile.source_reference = candidate.source_reference
            source_reference = candidate.source_reference or candidate.storage_path or "unknown"
            record = await session.scalar(
                select(CandidateSourceRecord).where(
                    CandidateSourceRecord.candidate_id == user.id,
                    CandidateSourceRecord.source_type == candidate.source_type,
                    CandidateSourceRecord.source_reference == source_reference,
                )
            )
            if record:
                record.last_seen_at = datetime.now(UTC)
                record.source_metadata = {
                    "verification_status": candidate.verification_status,
                    "agent_processing_allowed": True,
                }
            else:
                session.add(CandidateSourceRecord(
                    candidate_id=user.id,
                    source_type=candidate.source_type,
                    source_reference=source_reference,
                    source_metadata={
                        "verification_status": candidate.verification_status,
                        "agent_processing_allowed": True,
                    },
                ))
            resume = await session.scalar(
                select(Resume).where(
                    Resume.candidate_id == user.id,
                    Resume.storage_path == candidate.storage_path,
                )
            )
            if not resume:
                resume = Resume(
                    candidate_id=user.id,
                    filename=Path(candidate.storage_path).name,
                    original_filename=candidate.original_filename,
                    file_size=candidate.file_size,
                    file_type=candidate.file_type,
                    storage_path=candidate.storage_path,
                )
                session.add(resume)
                await session.flush()
            parsed = await session.scalar(
                select(ParsedResume).where(ParsedResume.resume_id == resume.resume_id)
            )
            if not parsed:
                data = parse_resume_text(candidate.raw_text)
                session.add(ParsedResume(
                    resume_id=resume.resume_id,
                    candidate_id=user.id,
                    skills=",".join(data.skills),
                    total_experience_years=max(
                        data.total_experience_years,
                        candidate.total_experience or 0,
                    ),
                    education=",".join(data.education),
                    certifications=",".join(data.certifications),
                    projects="\n".join(data.projects),
                    sections=data.sections,
                    raw_text=data.raw_text,
                ))
            updated += 1
        await session.commit()
    print(f"Authorized sources synchronized: {updated}; missing profiles: {missing}; skipped: {skipped}")


if __name__ == "__main__":
    asyncio.run(main())
