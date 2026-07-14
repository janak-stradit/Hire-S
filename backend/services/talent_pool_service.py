from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import and_, exists, false, func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from backend.excel_intake.service import CandidateFetchCriteria, ExcelIntakeService, requires_distribution_audit
from backend.excel_intake.workbooks import read_requirement
from backend.models.application import Application
from backend.models.candidate import CandidateLifecycleEvent, CandidateProfile
from backend.models.user import User
from backend.models.validator import ExcelIntakeBatch, ParsedResume
from backend.schemas.talent_pool import TalentPoolScreenRequest
from backend.validator.contracts import Thresholds
from backend.validator.service import ValidatorService
from backend.services.batch_tracking_service import track_validator_result

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIREMENT_WORKBOOK = PROJECT_ROOT / "storage/job_requirements/jd_input.xlsx"


class TalentPoolService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def summary(self) -> dict[str, int]:
        await self._mark_stale_profiles()
        rows = (
            await self.session.execute(
                select(CandidateProfile.talent_pool_status, func.count())
                .where(
                    CandidateProfile.reusable_from_pool.is_(True),
                    CandidateProfile.agent_processing_allowed.is_(True),
                )
                .group_by(CandidateProfile.talent_pool_status)
            )
        ).all()
        counts = {status: count for status, count in rows}
        screen_ready = await self.session.scalar(
            select(func.count(func.distinct(CandidateProfile.candidate_id)))
            .join(ParsedResume, ParsedResume.candidate_id == CandidateProfile.candidate_id)
            .where(
                CandidateProfile.talent_pool_status == "AVAILABLE",
                CandidateProfile.reusable_from_pool.is_(True),
                CandidateProfile.agent_processing_allowed.is_(True),
            )
        )
        simulation_screen_ready = await self.session.scalar(
            select(func.count(func.distinct(CandidateProfile.candidate_id)))
            .join(ParsedResume, ParsedResume.candidate_id == CandidateProfile.candidate_id)
            .where(
                CandidateProfile.talent_pool_status == "AVAILABLE",
                CandidateProfile.source_type == "synthetic",
            )
        )
        return {
            "total": sum(counts.values()),
            "available": counts.get("AVAILABLE", 0),
            "screen_ready": screen_ready or 0,
            "simulation_screen_ready": simulation_screen_ready or 0,
            "refresh_required": counts.get("REFRESH_REQUIRED", 0),
            "in_process": counts.get("IN_PROCESS", 0),
            "hired": counts.get("HIRED", 0),
            "do_not_contact": counts.get("DO_NOT_CONTACT", 0),
        }

    async def screen(self, actor: User, payload: TalentPoolScreenRequest) -> dict:
        await self._mark_stale_profiles()
        requirement = read_requirement(REQUIREMENT_WORKBOOK, payload.requirement_id)
        job = await ExcelIntakeService(self.session)._upsert_job(actor, requirement)
        batch = ExcelIntakeBatch(
            requirement_id=requirement.requirement_id,
            job_id=job.job_id,
            candidate_workbook="database://reusable-talent-pool",
            requirement_workbook=str(REQUIREMENT_WORKBOOK),
            status="RUNNING",
        )
        self.session.add(batch)
        await self.session.commit()
        batch_id = batch.batch_id

        latest_parsed = (
            select(
                ParsedResume.candidate_id,
                func.max(ParsedResume.parsed_at).label("parsed_at"),
            )
            .group_by(ParsedResume.candidate_id)
            .subquery()
        )
        rows = (
            await self.session.execute(
                select(CandidateProfile, ParsedResume)
                .join(latest_parsed, latest_parsed.c.candidate_id == CandidateProfile.candidate_id)
                .join(
                    ParsedResume,
                    (ParsedResume.candidate_id == latest_parsed.c.candidate_id)
                    & (ParsedResume.parsed_at == latest_parsed.c.parsed_at),
                )
                .where(
                    CandidateProfile.talent_pool_status == "AVAILABLE",
                    CandidateProfile.profile_freshness_status == "FRESH",
                    CandidateProfile.profile_refresh_due_at > datetime.now(UTC),
                    or_(
                        and_(
                            true() if payload.simulation_mode else false(),
                            CandidateProfile.source_type == "synthetic",
                        ),
                        and_(
                            false() if payload.simulation_mode else true(),
                            CandidateProfile.reusable_from_pool.is_(True),
                            CandidateProfile.agent_processing_allowed.is_(True),
                        ),
                    ),
                    ~exists().where(
                        (Application.candidate_id == CandidateProfile.candidate_id)
                        & (Application.job_id == job.job_id)
                    ),
                )
                .order_by(CandidateProfile.last_evaluated_at.asc())
                .limit(payload.max_candidates)
            )
        ).all()
        criteria = CandidateFetchCriteria(requirement)
        eligible_rows = [
            (profile, parsed) for profile, parsed in rows
            if criteria.matches(profile, parsed.raw_text)
        ]
        eligible_rows.sort(key=lambda item: criteria.source_rank(item[0]))
        batch.candidates_read = len(rows)
        decisions: list[str] = []

        try:
            thresholds = Thresholds(
                pass_score=requirement.screening_pass_score,
                review_score=requirement.screening_review_score,
            )
            for profile, parsed in eligible_rows:
                application = Application(
                    candidate_id=profile.candidate_id,
                    job_id=job.job_id,
                    application_status="POOL_REUSED",
                    intake_source="talent_pool",
                    intake_batch_id=batch_id,
                )
                self.session.add(application)
                await self.session.flush()
                evaluation = await ValidatorService(self.session).evaluate_application(
                    application.application_id,
                    thresholds=thresholds,
                    resume_text_override=parsed.raw_text,
                    commit=False,
                )
                await track_validator_result(
                    self.session,
                    batch_id=batch_id,
                    application_id=application.application_id,
                    candidate_id=evaluation.candidate_id,
                    job_id=evaluation.job_id,
                    validator_result_id=evaluation.validator_result_id,
                    decision=evaluation.decision,
                    final_score=evaluation.scores.final_score,
                    source_kind="SYNTHETIC_POOL" if payload.simulation_mode else "TALENT_POOL",
                )
                decisions.append(evaluation.decision)

            batch.candidates_imported = len(decisions)
            batch.pass_count = decisions.count("PASS")
            batch.review_count = decisions.count("REVIEW")
            batch.fail_count = decisions.count("FAIL")
            batch.status = "COMPLETED"
            if requires_distribution_audit([{"decision": value} for value in decisions]):
                batch.status = "AUDIT_REQUIRED"
                batch.error_report = "No reusable candidate reached REVIEW; audit fit before external sourcing."
            batch.completed_at = datetime.now(UTC)
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            persisted = await self.session.get(ExcelIntakeBatch, batch_id)
            if persisted:
                persisted.status = "FAILED"
                persisted.error_report = str(exc)[:4000]
                persisted.completed_at = datetime.now(UTC)
                await self.session.commit()
            raise

        return {
            "batch_id": batch.batch_id,
            "requirement_id": requirement.requirement_id,
            "job_id": job.job_id,
            "status": batch.status,
            "pool_candidates_considered": len(rows),
            "pool_candidates_evaluated": len(decisions),
            "pass_count": batch.pass_count,
            "review_count": batch.review_count,
            "fail_count": batch.fail_count,
            "remaining_requested": max(payload.max_candidates - len(decisions), 0),
        }

    async def release(self, candidate_id: str, reason: str, outcome: str) -> dict:
        profile = await self.session.get(CandidateProfile, candidate_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Candidate not found")
        previous = profile.talent_pool_status
        now = datetime.now(UTC)
        if profile.profile_refresh_due_at <= now:
            profile.talent_pool_status = "REFRESH_REQUIRED"
            profile.profile_freshness_status = "STALE"
        else:
            profile.talent_pool_status = "AVAILABLE"
            profile.profile_freshness_status = "FRESH"
        profile.reusable_from_pool = profile.agent_processing_allowed
        profile.last_outcome = outcome
        self.session.add(CandidateLifecycleEvent(
            candidate_id=candidate_id,
            event_type="RETURNED_TO_POOL",
            from_status=previous,
            to_status=profile.talent_pool_status,
            reason=reason.strip(),
            event_metadata={"outcome": outcome},
        ))
        await self.session.commit()
        return {
            "candidate_id": candidate_id,
            "talent_pool_status": profile.talent_pool_status,
            "outcome": outcome,
        }

    async def _mark_stale_profiles(self) -> int:
        now = datetime.now(UTC)
        profiles = list((await self.session.scalars(
            select(CandidateProfile).where(
                CandidateProfile.talent_pool_status == "AVAILABLE",
                CandidateProfile.reusable_from_pool.is_(True),
                CandidateProfile.agent_processing_allowed.is_(True),
                CandidateProfile.profile_refresh_due_at <= now,
            )
        )).all())
        for profile in profiles:
            profile.talent_pool_status = "REFRESH_REQUIRED"
            profile.profile_freshness_status = "STALE"
            self.session.add(CandidateLifecycleEvent(
                candidate_id=profile.candidate_id,
                event_type="PROFILE_REFRESH_REQUIRED",
                from_status="AVAILABLE",
                to_status="REFRESH_REQUIRED",
                reason="Candidate profile exceeded the 30-day freshness window.",
                event_metadata={
                    "profile_last_refreshed_at": profile.profile_last_refreshed_at.isoformat(),
                    "profile_refresh_due_at": profile.profile_refresh_due_at.isoformat(),
                },
            ))
        if profiles:
            await self.session.commit()
        return len(profiles)
