"""Reset HireX hiring runtime data while preserving schema and manager accounts."""

# ruff: noqa: E402

import argparse
import asyncio
from pathlib import Path
import sys

from sqlalchemy import delete, func, select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.database.session import AsyncSessionLocal
from backend.models.application import Application
from backend.models.candidate import (
    CandidateBatchMembership,
    CandidateIdentity,
    CandidateLifecycleEvent,
    CandidateProfile,
    CandidateSourceRecord,
    CandidateStageEvent,
)
from backend.models.hr_review import HRReviewAction
from backend.models.job import Job
from backend.models.resume import Resume
from backend.models.user import User
from backend.models.validator import ExcelIntakeBatch, ParsedJobDescription, ParsedResume, ValidatorResult

MODELS_IN_DELETE_ORDER = [
    CandidateStageEvent,
    CandidateBatchMembership,
    HRReviewAction,
    ValidatorResult,
    CandidateLifecycleEvent,
    ParsedJobDescription,
    ParsedResume,
    Application,
    ExcelIntakeBatch,
    CandidateIdentity,
    CandidateSourceRecord,
    Resume,
    CandidateProfile,
    Job,
]


async def reset(execute: bool) -> None:
    async with AsyncSessionLocal() as session:
        counts = {
            model.__tablename__: int(
                (await session.scalar(select(func.count()).select_from(model))) or 0
            )
            for model in MODELS_IN_DELETE_ORDER
        }
        counts["candidate_users"] = int(
            (await session.scalar(select(func.count()).select_from(User).where(User.role == "candidate")))
            or 0
        )
        for table, count in counts.items():
            print(f"{table}: {count}")
        if not execute:
            print("Dry run only. Pass --execute to commit the reset.")
            return
        for model in MODELS_IN_DELETE_ORDER:
            await session.execute(delete(model))
        await session.execute(delete(User).where(User.role == "candidate"))
        await session.commit()
        print("Runtime reset committed; manager accounts and schema were preserved.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    asyncio.run(reset(args.execute))


if __name__ == "__main__":
    main()
