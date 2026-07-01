"""Quarantine a validator batch so it cannot drive HR decisions."""

import argparse
import asyncio
from pathlib import Path
import sys

from sqlalchemy import select, update

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.database.session import AsyncSessionLocal
from backend.models.application import Application
from backend.models.validator import ExcelIntakeBatch


async def quarantine(batch_id: str, reason: str) -> None:
    async with AsyncSessionLocal() as session:
        batch = await session.scalar(
            select(ExcelIntakeBatch).where(ExcelIntakeBatch.batch_id == batch_id)
        )
        if not batch:
            raise RuntimeError("Validator batch not found")
        batch.status = "AUDIT_REQUIRED"
        batch.error_report = reason
        await session.execute(
            update(Application)
            .where(Application.intake_batch_id == batch_id)
            .values(application_status="VALIDATOR_AUDIT_REQUIRED")
        )
        await session.commit()
        print(f"Batch {batch_id} quarantined.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()
    asyncio.run(quarantine(args.batch, args.reason))


if __name__ == "__main__":
    main()
