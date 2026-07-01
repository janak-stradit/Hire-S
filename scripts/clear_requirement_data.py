"""Delete PostgreSQL records owned by one Excel job requirement."""

import argparse
import asyncio
from pathlib import Path
import sys

from sqlalchemy import delete, func, select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.database.session import AsyncSessionLocal
from backend.models.application import Application
from backend.models.hr_review import HRReviewAction
from backend.models.job import Job
from backend.models.validator import (
    ExcelIntakeBatch,
    ParsedJobDescription,
    ParsedResume,
    ValidatorResult,
)


async def scalar_count(session, model, condition) -> int:
    return int((await session.scalar(select(func.count()).select_from(model).where(condition))) or 0)


async def clear(requirement_id: str, execute: bool) -> None:
    async with AsyncSessionLocal() as session:
        job_ids = list(
            (
                await session.scalars(select(Job.job_id).where(Job.requirement_id == requirement_id))
            ).all()
        )
        if not job_ids:
            print(f"No PostgreSQL job found for requirement {requirement_id}")
            return

        application_ids = list(
            (
                await session.scalars(
                    select(Application.application_id).where(Application.job_id.in_(job_ids))
                )
            ).all()
        )
        result_rows = (
            await session.execute(
                select(
                    ValidatorResult.validator_result_id,
                    ValidatorResult.parsed_resume_id,
                    ValidatorResult.parsed_jd_id,
                ).where(ValidatorResult.job_id.in_(job_ids))
            )
        ).all()
        result_ids = [row.validator_result_id for row in result_rows]
        parsed_resume_ids = list({row.parsed_resume_id for row in result_rows})

        counts = {
            "jobs": len(job_ids),
            "intake_batches": await scalar_count(
                session,
                ExcelIntakeBatch,
                ExcelIntakeBatch.requirement_id == requirement_id,
            ),
            "applications": len(application_ids),
            "validator_results": len(result_ids),
            "hr_review_actions": await scalar_count(
                session,
                HRReviewAction,
                HRReviewAction.application_id.in_(application_ids),
            ) if application_ids else 0,
            "parsed_resumes": len(parsed_resume_ids),
            "parsed_job_descriptions": await scalar_count(
                session,
                ParsedJobDescription,
                ParsedJobDescription.job_id.in_(job_ids),
            ),
        }
        print(f"Requirement: {requirement_id}")
        for label, count in counts.items():
            print(f"{label}: {count}")
        if not execute:
            print("Dry run only. Pass --execute to delete these records.")
            return

        if application_ids:
            await session.execute(
                delete(HRReviewAction).where(HRReviewAction.application_id.in_(application_ids))
            )
        if result_ids:
            await session.execute(
                delete(ValidatorResult).where(ValidatorResult.validator_result_id.in_(result_ids))
            )
        if parsed_resume_ids:
            await session.execute(
                delete(ParsedResume).where(ParsedResume.parsed_resume_id.in_(parsed_resume_ids))
            )
        await session.execute(
            delete(ParsedJobDescription).where(ParsedJobDescription.job_id.in_(job_ids))
        )
        await session.execute(delete(Application).where(Application.job_id.in_(job_ids)))
        await session.execute(
            delete(ExcelIntakeBatch).where(ExcelIntakeBatch.requirement_id == requirement_id)
        )
        await session.execute(delete(Job).where(Job.job_id.in_(job_ids)))
        await session.commit()
        print("Deletion committed.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requirement", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    asyncio.run(clear(args.requirement, args.execute))


if __name__ == "__main__":
    main()
