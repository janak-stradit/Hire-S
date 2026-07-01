"""Verify persisted validator invariants for one Excel intake batch."""

import argparse
import asyncio
from collections import Counter
from pathlib import Path
import sys

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.database.session import AsyncSessionLocal
from backend.models.application import Application
from backend.models.job import Job
from backend.models.validator import ExcelIntakeBatch, ParsedResume, ValidatorResult

REQUIRED_RESUME_SECTIONS = {
    "summary", "experience", "skills", "education", "projects", "certifications"
}


async def verify(batch_id: str) -> None:
    async with AsyncSessionLocal() as session:
        batch = await session.get(ExcelIntakeBatch, batch_id)
        if not batch or batch.status != "COMPLETED":
            raise RuntimeError("Batch is missing or not completed")
        rows = (
            await session.execute(
                select(Application, ValidatorResult, ParsedResume)
                .join(ValidatorResult, ValidatorResult.application_id == Application.application_id)
                .join(ParsedResume, ParsedResume.parsed_resume_id == ValidatorResult.parsed_resume_id)
                .where(ValidatorResult.intake_batch_id == batch_id)
            )
        ).all()
        if len(rows) != batch.candidates_imported:
            raise RuntimeError(f"Expected {batch.candidates_imported} results, found {len(rows)}")
        if any(result.scoring_version != "2.3" for _, result, _ in rows):
            raise RuntimeError("Batch contains an unexpected scoring version")
        decisions = Counter(result.decision for _, result, _ in rows)
        expected = {"PASS": batch.pass_count, "REVIEW": batch.review_count, "FAIL": batch.fail_count}
        if dict(decisions) != {key: value for key, value in expected.items() if value}:
            raise RuntimeError(f"Decision counts differ: {dict(decisions)} != {expected}")
        if any(not (result.matched_skills or result.missing_skills) for _, result, _ in rows):
            raise RuntimeError("One or more results have no required-skill evidence")
        if any(not parsed.sections for _, _, parsed in rows):
            raise RuntimeError("One or more parsed resumes have no structured sections")
        if any(
            not REQUIRED_RESUME_SECTIONS.issubset(parsed.sections)
            or any(not parsed.sections[section].strip() for section in REQUIRED_RESUME_SECTIONS)
            or not parsed.raw_text.strip()
            for _, _, parsed in rows
        ):
            raise RuntimeError("One or more resumes are missing required content sections or raw text")
        expected_status = {"PASS": "SHORTLISTED", "REVIEW": "UNDER_REVIEW", "FAIL": "REJECTED"}
        if any(app.application_status != expected_status[result.decision] for app, result, _ in rows):
            raise RuntimeError("Application status does not match validator decision")
        job = await session.get(Job, batch.job_id)
        required_skill_count = len(
            [skill for skill in (job.skills_required or "").split(",") if skill.strip()]
        )
        rejected = [(app, result, parsed) for app, result, parsed in rows if result.decision == "FAIL"]
        if any(result.final_score >= job.screening_review_score for _, result, _ in rejected):
            raise RuntimeError("A rejected candidate meets or exceeds the review threshold")
        if any(
            len(result.matched_skills) + len(result.missing_skills) != required_skill_count
            for _, result, _ in rejected
        ):
            raise RuntimeError("A rejected candidate has incomplete required-skill mapping")
        print(f"Batch {batch_id}: VERIFIED")
        print(f"Results: {len(rows)}; decisions: {dict(decisions)}")
        print(f"Rejected candidates fully audited: {len(rejected)}")
        print("Evidence, resume sections, scoring version, and application statuses are consistent.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()
    asyncio.run(verify(args.batch))


if __name__ == "__main__":
    main()
