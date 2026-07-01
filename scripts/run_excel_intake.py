"""Run a reviewed Excel intake configuration from the command line."""

import argparse
import asyncio
from pathlib import Path
import sys

from sqlalchemy import select, update

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.database.session import AsyncSessionLocal
from backend.excel_intake.contracts import ExcelIntakeRequest
from backend.excel_intake.service import ExcelIntakeService
from backend.models.user import User
from backend.models.validator import ExcelIntakeBatch


async def run(email: str, pool: str, requirement_id: str) -> None:
    async with AsyncSessionLocal() as session:
        actor = (
            await session.execute(select(User).where(User.email == email.casefold()))
        ).scalar_one_or_none()
        if not actor or actor.role not in {"admin", "hr", "recruiter"}:
            raise RuntimeError("A valid HR, recruiter, or admin email is required")
        result = await ExcelIntakeService(session).run(
            actor,
            ExcelIntakeRequest(candidate_pool=pool, requirement_id=requirement_id),
        )
        await session.execute(
            update(ExcelIntakeBatch)
            .where(
                ExcelIntakeBatch.requirement_id == requirement_id,
                ExcelIntakeBatch.batch_id != result.batch_id,
                ExcelIntakeBatch.status == "COMPLETED",
            )
            .values(status="SUPERSEDED")
        )
        await session.commit()
        print(result.model_dump_json(indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--pool", choices=("real", "synthetic"), required=True)
    parser.add_argument("--requirement", required=True)
    args = parser.parse_args()
    asyncio.run(run(args.email, args.pool, args.requirement))


if __name__ == "__main__":
    main()
