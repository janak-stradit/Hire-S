"""Excel candidate intake orchestration.

This service is the MVP bridge between file-based sourcing and the HireX core
database. It reads the selected JD and candidate workbook, deduplicates candidate
identity, creates one auditable batch, validates each candidate, exports
shortlisted/rejected workbooks, and leaves dashboard-ready records in Postgres.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import re
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.excel_intake.contracts import CandidateIntakeRow, ExcelIntakeRequest, ExcelIntakeResult, JobRequirementRow
from backend.excel_intake.workbooks import export_results, read_candidates, read_requirement
from backend.models.application import Application
from backend.models.candidate import (
    CandidateBatchMembership,
    CandidateIdentity,
    CandidateLifecycleEvent,
    CandidateProfile,
    CandidateRefreshChange,
    CandidateSourceRecord,
    CandidateStageEvent,
    SourcingBatch,
)
from backend.models.hr_review import HRReviewAction
from backend.models.job import Job
from backend.models.resume import Resume
from backend.models.user import User
from backend.models.validator import ExcelIntakeBatch, ParsedJobDescription, ParsedResume, ValidatorResult
from backend.services.candidate_identity_service import CandidateIdentityService
from backend.services.batch_tracking_service import track_validator_result
from backend.validator.contracts import Thresholds
from backend.validator.service import ValidatorService

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STORAGE_ROOT = PROJECT_ROOT / "storage"
PROFILE_REFRESH_INTERVAL_DAYS = 30
CANDIDATE_POOL_FILES = {
    "real": {
        "label": "Extracted real resumes",
        "path": Path("storage/candidate_pool/hirex_candidates.xlsx"),
        "include_synthetic": False,
        "simulation_only": False,
    },
    "synthetic": {
        "label": "Synthetic simulation pool",
        "path": Path("storage/candidate_pool/test_synthetic_candidates.xlsx"),
        "include_synthetic": True,
        "simulation_only": True,
    },
    "freshness_wave1": {
        "label": "Freshness wave 1 - 300 refreshed",
        "path": Path("storage/candidate_pool/freshness_cycles/hirex_freshness_wave1_300_refreshed.xlsx"),
        "include_synthetic": True,
        "simulation_only": True,
    },
    "freshness_wave2": {
        "label": "Freshness wave 2 - 200 refreshed + 300 new",
        "path": Path("storage/candidate_pool/freshness_cycles/hirex_freshness_wave2_200_refreshed_300_new.xlsx"),
        "include_synthetic": True,
        "simulation_only": True,
    },
    "freshness_wave3": {
        "label": "Freshness wave 3 - 100 refreshed + 200 new",
        "path": Path("storage/candidate_pool/freshness_cycles/hirex_freshness_wave3_100_refreshed_200_new.xlsx"),
        "include_synthetic": True,
        "simulation_only": True,
    },
}


class ExcelIntakeService:
    """Coordinate a full validator batch from HR input to persisted results."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def run(self, actor: User, payload: ExcelIntakeRequest) -> ExcelIntakeResult:
        """Run one HR-triggered intake batch.

        Entry point: `POST /api/excel-intake/run`.
        End point: `ExcelIntakeBatch`, `ValidatorResult`, `CandidateBatchMembership`,
        output workbooks, and dashboard counts are all updated for the selected JD.
        """
        if actor.role not in {"recruiter", "hr", "admin"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Job manager role required")
        if payload.candidate_pool:
            pool = CANDIDATE_POOL_FILES.get(payload.candidate_pool)
            if not pool:
                raise HTTPException(status_code=400, detail=f"Unknown candidate pool: {payload.candidate_pool}")
            payload.candidate_workbook = pool["path"]
            payload.include_synthetic = bool(pool["include_synthetic"])
        candidate_path = self._storage_path(payload.candidate_workbook)
        requirement_path = self._storage_path(payload.requirement_workbook)
        requirement = read_requirement(requirement_path, payload.requirement_id)
        candidates, skipped = read_candidates(candidate_path, payload.include_synthetic)

        # Guardrail: prevent two overlapping runs for the same JD from creating
        # duplicate memberships, conflicting application states, or confusing HR
        # counts on the dashboard.
        active_batch = await self.session.scalar(
            select(ExcelIntakeBatch)
            .where(
                ExcelIntakeBatch.requirement_id == requirement.requirement_id,
                ExcelIntakeBatch.status == "RUNNING",
                ExcelIntakeBatch.started_at >= datetime.now(UTC) - timedelta(minutes=30),
            )
            .order_by(ExcelIntakeBatch.started_at.desc())
            .limit(1)
        )
        if active_batch:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Validator batch {active_batch.batch_id} is already running for this requirement",
            )

        # Any old RUNNING batch outside the execution window is marked failed so
        # the UI can recover cleanly after an interrupted request or server stop.
        stale_batches = await self.session.scalars(
            select(ExcelIntakeBatch).where(
                ExcelIntakeBatch.requirement_id == requirement.requirement_id,
                ExcelIntakeBatch.status == "RUNNING",
            )
        )
        for stale_batch in stale_batches:
            stale_batch.status = "FAILED"
            stale_batch.error_report = "Batch exceeded the 30-minute execution window and was retired."
            stale_batch.completed_at = datetime.now(UTC)

        batch = ExcelIntakeBatch(
            requirement_id=requirement.requirement_id,
            candidate_workbook=str(candidate_path),
            requirement_workbook=str(requirement_path),
            candidates_read=len(candidates) + skipped,
            candidates_skipped=skipped,
        )
        self.session.add(batch)
        await self.session.commit()
        batch_id = batch.batch_id

        try:
            job = await self._upsert_job(actor, requirement)
            batch.job_id = job.job_id
            # SourcingBatch preserves where this candidate cluster came from.
            # The same shape can later represent Naukri, LinkedIn, ATS, or portal
            # imports instead of local Excel workbooks.
            sourcing_batch = SourcingBatch(
                source_type=payload.candidate_pool or "excel",
                source_reference=str(payload.candidate_workbook),
                source_label=f"{requirement.role} sourcing input",
                total_candidates=len(candidates),
                metadata_json={
                    "requirement_id": requirement.requirement_id,
                    "intake_batch_id": batch_id,
                    "candidate_pool": payload.candidate_pool or "custom",
                },
            )
            self.session.add(sourcing_batch)
            await self.session.flush()
            imports: list[tuple[Application, dict, str]] = []
            imported_candidate_ids: set[str] = set()
            candidate_filters = CandidateFetchCriteria(requirement)
            matching_candidates = [
                candidate for candidate in candidates
                if candidate_filters.matches(candidate, candidate.raw_text)
            ]
            matching_candidates.sort(key=candidate_filters.source_rank)
            batch.candidates_skipped += len(candidates) - len(matching_candidates)
            for candidate in candidates:
                if candidate not in matching_candidates:
                    continue
                # Candidate identity is resolved before validation so the same
                # person is stored once and reused across many job batches.
                application, created_for_job, profile_created, refreshed = (
                    await self._upsert_candidate_application(candidate, job, batch_id, sourcing_batch)
                )
                if profile_created:
                    sourcing_batch.new_candidates += 1
                else:
                    sourcing_batch.known_candidates += 1
                if refreshed:
                    sourcing_batch.refreshed_candidates += 1
                if not created_for_job:
                    batch.candidates_skipped += 1
                    continue
                if application.candidate_id in imported_candidate_ids:
                    batch.candidates_skipped += 1
                    continue
                imported_candidate_ids.add(application.candidate_id)
                imports.append((application, candidate.model_dump(), candidate.raw_text))
                if len(imports) >= payload.max_candidates:
                    break
            batch.candidates_imported = len(imports)
            await self.session.commit()

            thresholds = Thresholds(
                pass_score=requirement.screening_pass_score,
                review_score=requirement.screening_review_score,
            )
            result_rows: list[dict] = []
            for application, candidate, raw_text in imports:
                # ValidatorService owns parsing/scoring/decision. The intake
                # service only supplies the resume text override and records the
                # batch membership around the returned evaluation.
                evaluation = await ValidatorService(self.session).evaluate_application(
                    application.application_id,
                    thresholds=thresholds,
                    resume_text_override=raw_text,
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
                    source_kind="SYNTHETIC" if candidate["source_type"] == "synthetic" else "EXTERNAL",
                )
                result_rows.append(self._result_row(batch, requirement.requirement_id, candidate, evaluation))

            await self.session.commit()

            # HR still receives familiar Excel outputs, but Postgres remains the
            # system of record for dashboards, rejected-pool reuse, and agents.
            shortlisted = [row for row in result_rows if row["decision"] in {"PASS", "REVIEW"}]
            rejected = [row for row in result_rows if row["decision"] == "FAIL"]
            output_stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            shortlist_path = STORAGE_ROOT / "shortlisted" / f"{requirement.requirement_id}_{output_stamp}.xlsx"
            rejected_path = STORAGE_ROOT / "rejected" / f"{requirement.requirement_id}_{output_stamp}.xlsx"
            export_results(shortlist_path, shortlisted, "Shortlisted_Candidates")
            export_results(rejected_path, rejected, "Rejected_Candidates")

            batch.status = "COMPLETED"
            batch.pass_count = sum(row["decision"] == "PASS" for row in result_rows)
            batch.review_count = sum(row["decision"] == "REVIEW" for row in result_rows)
            batch.fail_count = len(rejected)
            batch.shortlisted_workbook = str(shortlist_path)
            if requires_distribution_audit(result_rows):
                # If everyone fails, we stop HR actions and force a data/JD audit.
                # This protects the system from silently rejecting a whole batch
                # because of a bad JD, bad extraction, or wrong source file.
                batch.status = "AUDIT_REQUIRED"
                batch.error_report = (
                    "No candidate reached the REVIEW threshold. The candidate pool and job "
                    "requirement must be audited before HR decisions are allowed."
                )
                for application, _, _ in imports:
                    application.application_status = "VALIDATOR_AUDIT_REQUIRED"
            batch.completed_at = datetime.now(UTC)
            await self.session.commit()
            return ExcelIntakeResult(
                batch_id=batch.batch_id,
                requirement_id=requirement.requirement_id,
                job_id=job.job_id,
                status=batch.status,
                candidates_read=batch.candidates_read,
                candidates_imported=batch.candidates_imported,
                candidates_skipped=batch.candidates_skipped,
                pass_count=batch.pass_count,
                review_count=batch.review_count,
                fail_count=batch.fail_count,
                shortlisted_workbook=str(shortlist_path),
                rejected_workbook=str(rejected_path),
            )
        except Exception as exc:
            await self.session.rollback()
            persisted = await self.session.get(ExcelIntakeBatch, batch_id)
            if persisted:
                persisted.status = "FAILED"
                persisted.error_report = str(exc)[:4000]
                persisted.completed_at = datetime.now(UTC)
                await self.session.commit()
            raise

    async def get_batch(self, batch_id: str) -> ExcelIntakeBatch:
        """Fetch a batch by ID for the batch details dashboard."""
        batch = await self.session.get(ExcelIntakeBatch, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Excel intake batch not found")
        return batch

    async def get_latest_batch(self, requirement_id: str) -> ExcelIntakeBatch | None:
        return await self.session.scalar(
            select(ExcelIntakeBatch)
            .where(ExcelIntakeBatch.requirement_id == requirement_id)
            .order_by(ExcelIntakeBatch.started_at.desc())
            .limit(1)
        )

    async def list_batches(self, requirement_id: str | None = None) -> list[ExcelIntakeBatch]:
        """Return recent batches, optionally scoped to one JD requirement."""
        statement = select(ExcelIntakeBatch).order_by(ExcelIntakeBatch.started_at.desc())
        if requirement_id:
            statement = statement.where(ExcelIntakeBatch.requirement_id == requirement_id)
        return list((await self.session.scalars(statement.limit(200))).all())

    async def delete_batch(self, batch_id: str) -> dict[str, int | str]:
        """Delete one completed/failed batch and its dependent runtime records.

        This is intentionally scoped to batch runtime data. Candidate master
        records are only removed when they are no longer referenced elsewhere.
        """
        batch = await self.get_batch(batch_id)
        if batch.status in {"RUNNING", "QUEUED"}:
            raise HTTPException(status_code=409, detail="A running validator batch cannot be deleted")

        results = list((await self.session.scalars(
            select(ValidatorResult).where(ValidatorResult.intake_batch_id == batch_id)
        )).all())
        result_ids = [item.validator_result_id for item in results]
        parsed_resume_ids = [item.parsed_resume_id for item in results]
        parsed_jd_ids = [item.parsed_jd_id for item in results]
        candidate_ids = set(item.candidate_id for item in results)
        application_ids = set(item.application_id for item in results)
        application_ids.update((await self.session.scalars(
            select(CandidateBatchMembership.application_id).where(
                CandidateBatchMembership.batch_id == batch_id
            )
        )).all())
        candidate_ids.update((await self.session.scalars(
            select(CandidateBatchMembership.candidate_id).where(
                CandidateBatchMembership.batch_id == batch_id
            )
        )).all())

        if result_ids:
            await self.session.execute(
                delete(HRReviewAction).where(HRReviewAction.validator_result_id.in_(result_ids))
            )
        sourcing_batches = (await self.session.scalars(select(SourcingBatch))).all()
        sourcing_batch_ids = [
            item.sourcing_batch_id
            for item in sourcing_batches
            if (item.metadata_json or {}).get("intake_batch_id") == batch_id
        ]
        if sourcing_batch_ids:
            await self.session.execute(
                delete(CandidateRefreshChange).where(
                    CandidateRefreshChange.sourcing_batch_id.in_(sourcing_batch_ids)
                )
            )
            await self.session.execute(
                delete(SourcingBatch).where(SourcingBatch.sourcing_batch_id.in_(sourcing_batch_ids))
            )
        await self.session.execute(
            delete(CandidateStageEvent).where(CandidateStageEvent.batch_id == batch_id)
        )
        await self.session.execute(
            delete(CandidateBatchMembership).where(CandidateBatchMembership.batch_id == batch_id)
        )
        await self.session.execute(
            delete(ValidatorResult).where(ValidatorResult.intake_batch_id == batch_id)
        )
        if parsed_resume_ids:
            await self.session.execute(
                delete(ParsedResume).where(ParsedResume.parsed_resume_id.in_(parsed_resume_ids))
            )
        if parsed_jd_ids:
            await self.session.execute(
                delete(ParsedJobDescription).where(
                    ParsedJobDescription.parsed_jd_id.in_(parsed_jd_ids)
                )
            )

        applications_deleted = 0
        for application_id in application_ids:
            await self.session.execute(
                delete(CandidateLifecycleEvent).where(
                    CandidateLifecycleEvent.application_id == application_id
                )
            )
            references = await self.session.scalar(
                select(func.count()).select_from(ValidatorResult).where(
                    ValidatorResult.application_id == application_id
                )
            )
            memberships = await self.session.scalar(
                select(func.count()).select_from(CandidateBatchMembership).where(
                    CandidateBatchMembership.application_id == application_id
                )
            )
            if not references and not memberships:
                applications_deleted += 1
                await self.session.execute(
                    delete(Application).where(Application.application_id == application_id)
                )

        candidates_deleted = 0
        for candidate_id in candidate_ids:
            application_count = await self.session.scalar(
                select(func.count()).select_from(Application).where(
                    Application.candidate_id == candidate_id
                )
            )
            result_count = await self.session.scalar(
                select(func.count()).select_from(ValidatorResult).where(
                    ValidatorResult.candidate_id == candidate_id
                )
            )
            membership_count = await self.session.scalar(
                select(func.count()).select_from(CandidateBatchMembership).where(
                    CandidateBatchMembership.candidate_id == candidate_id
                )
            )
            if application_count or result_count or membership_count:
                continue
            candidates_deleted += 1
            await self.session.execute(
                delete(CandidateLifecycleEvent).where(
                    CandidateLifecycleEvent.candidate_id == candidate_id
                )
            )
            await self.session.execute(
                delete(CandidateIdentity).where(CandidateIdentity.candidate_id == candidate_id)
            )
            await self.session.execute(
                delete(CandidateSourceRecord).where(
                    CandidateSourceRecord.candidate_id == candidate_id
                )
            )
            await self.session.execute(delete(Resume).where(Resume.candidate_id == candidate_id))
            await self.session.execute(
                delete(CandidateProfile).where(CandidateProfile.candidate_id == candidate_id)
            )
            await self.session.execute(
                delete(User).where(User.id == candidate_id, User.role == "candidate")
            )

        artifact_paths = [batch.shortlisted_workbook]
        if batch.shortlisted_workbook:
            artifact_paths.append(str(
                STORAGE_ROOT / "rejected" / Path(batch.shortlisted_workbook).name
            ))
        await self.session.delete(batch)
        await self.session.commit()

        artifacts_deleted = 0
        for artifact in artifact_paths:
            if not artifact:
                continue
            path = Path(artifact).resolve()
            if STORAGE_ROOT.resolve() in path.parents and path.is_file():
                path.unlink()
                artifacts_deleted += 1
        return {
            "batch_id": batch_id,
            "validator_results_deleted": len(result_ids),
            "applications_deleted": applications_deleted,
            "candidates_deleted": candidates_deleted,
            "artifacts_deleted": artifacts_deleted,
        }

    async def _upsert_job(self, actor, requirement) -> Job:
        result = await self.session.execute(select(Job).where(Job.requirement_id == requirement.requirement_id))
        job = result.scalar_one_or_none()
        values = {
            "title": requirement.role,
            "department": requirement.department,
            "location": requirement.location,
            "employment_type": requirement.employment_type,
            "experience_min": requirement.experience_min,
            "experience_max": requirement.experience_max,
            "salary_min": requirement.salary_min,
            "salary_max": requirement.salary_max,
            "description": requirement.jd_text,
            "skills_required": ",".join(requirement.required_skills),
            "preferred_skills": ",".join(requirement.preferred_skills),
            "education_requirements": requirement.education,
            "mandatory_certifications": ",".join(requirement.mandatory_certifications),
            "screening_pass_score": requirement.screening_pass_score,
            "screening_review_score": requirement.screening_review_score,
            "status": "open",
            "intake_source": "excel",
        }
        if job:
            for key, value in values.items():
                setattr(job, key, value)
            return job
        job = Job(requirement_id=requirement.requirement_id, created_by=actor.id, **values)
        self.session.add(job)
        await self.session.flush()
        return job

    async def _upsert_candidate_application(
        self, candidate, job: Job, batch_id: str, sourcing_batch: SourcingBatch | None = None
    ) -> tuple[Application, bool, bool, bool]:
        identity_service = CandidateIdentityService(self.session)
        user, user_created, identities = await identity_service.resolve_or_create_user(candidate)
        profile = await self.session.get(CandidateProfile, user.id)
        profile_created = profile is None
        refreshed_at = datetime.now(UTC)
        if profile_created:
            profile = CandidateProfile(candidate_id=user.id)
            self.session.add(profile)
        old_snapshot = self._profile_snapshot(profile) if not profile_created else {}
        for field in (
            "first_name", "last_name", "phone", "city", "state", "country", "current_company",
            "current_role", "total_experience", "expected_salary", "notice_period",
            "highest_education", "linkedin_url", "github_url", "portfolio_url",
        ):
            setattr(profile, field, getattr(candidate, field))
        if profile_created or candidate.agent_processing_allowed or not profile.agent_processing_allowed:
            profile.source_type = candidate.source_type
            profile.verification_status = candidate.verification_status
            profile.source_reference = candidate.source_reference
        profile.agent_processing_allowed = (
            bool(profile.agent_processing_allowed) or candidate.agent_processing_allowed
        )
        profile.profile_completion_percentage = 100
        source_refreshed_at = candidate.profile_last_updated_at or refreshed_at
        refresh_cycle_days = candidate.profile_refresh_cycle_days or PROFILE_REFRESH_INTERVAL_DAYS
        profile.profile_last_refreshed_at = source_refreshed_at
        profile.profile_refresh_due_at = source_refreshed_at + timedelta(days=refresh_cycle_days)
        profile.profile_freshness_status = "FRESH"
        if profile.last_outcome is None or profile.talent_pool_status in {"AVAILABLE", "REFRESH_REQUIRED"}:
            profile.talent_pool_status = "AVAILABLE"
            profile.reusable_from_pool = profile.agent_processing_allowed
        await self.session.flush()
        await identity_service.register(user.id, candidate.source_type, identities)

        source_reference = candidate.source_reference or candidate.storage_path or "unknown"
        source_record = await self.session.scalar(
            select(CandidateSourceRecord).where(
                CandidateSourceRecord.candidate_id == user.id,
                CandidateSourceRecord.source_type == candidate.source_type,
                CandidateSourceRecord.source_reference == source_reference,
            )
        )
        if source_record:
            source_record.last_seen_at = refreshed_at
            source_record.source_metadata = {
                **(source_record.source_metadata or {}),
                "verification_status": candidate.verification_status,
                "agent_processing_allowed": candidate.agent_processing_allowed,
                "profile_last_refreshed_at": source_refreshed_at.isoformat(),
                "profile_refresh_due_at": profile.profile_refresh_due_at.isoformat(),
                "preferred_work_mode": candidate.preferred_work_mode,
                "willing_to_relocate": candidate.willing_to_relocate,
                "preferred_locations": candidate.preferred_locations,
                "industry_domain": candidate.industry_domain,
                "profile_refresh_cycle_days": refresh_cycle_days,
            }
        else:
            self.session.add(CandidateSourceRecord(
                candidate_id=user.id,
                source_type=candidate.source_type,
                source_reference=source_reference,
                source_metadata={
                    "verification_status": candidate.verification_status,
                    "agent_processing_allowed": candidate.agent_processing_allowed,
                    "profile_last_refreshed_at": source_refreshed_at.isoformat(),
                    "profile_refresh_due_at": profile.profile_refresh_due_at.isoformat(),
                    "preferred_work_mode": candidate.preferred_work_mode,
                    "willing_to_relocate": candidate.willing_to_relocate,
                    "preferred_locations": candidate.preferred_locations,
                    "industry_domain": candidate.industry_domain,
                    "profile_refresh_cycle_days": refresh_cycle_days,
                },
            ))
            await self.session.flush()
            source_record = await self.session.scalar(
                select(CandidateSourceRecord).where(
                    CandidateSourceRecord.candidate_id == user.id,
                    CandidateSourceRecord.source_type == candidate.source_type,
                    CandidateSourceRecord.source_reference == source_reference,
                )
            )

        new_snapshot = self._profile_snapshot(profile)
        changed_fields = {} if profile_created else self._changed_fields(old_snapshot, new_snapshot)
        refreshed = bool(changed_fields)
        if not profile_created and changed_fields:
            self.session.add(CandidateRefreshChange(
                candidate_id=user.id,
                source_record_id=source_record.source_record_id if source_record else None,
                sourcing_batch_id=sourcing_batch.sourcing_batch_id if sourcing_batch else None,
                changed_fields=changed_fields,
                old_snapshot=old_snapshot,
                new_snapshot=new_snapshot,
                change_summary=self._change_summary(changed_fields),
            ))
            self.session.add(CandidateLifecycleEvent(
                candidate_id=user.id,
                event_type="PROFILE_REFRESHED",
                from_status=old_snapshot.get("talent_pool_status"),
                to_status=profile.talent_pool_status,
                reason=self._change_summary(changed_fields),
                event_metadata={
                    "changed_fields": list(changed_fields),
                    "sourcing_batch_id": sourcing_batch.sourcing_batch_id if sourcing_batch else None,
                },
            ))

        resume_result = await self.session.execute(
            select(Resume).where(Resume.candidate_id == user.id, Resume.storage_path == candidate.storage_path)
        )
        if not resume_result.scalar_one_or_none():
            self.session.add(Resume(
                candidate_id=user.id, filename=Path(candidate.storage_path).name,
                original_filename=candidate.original_filename, file_size=candidate.file_size,
                file_type=candidate.file_type, storage_path=candidate.storage_path,
            ))
            await self.session.flush()

        app_result = await self.session.execute(
            select(Application).where(Application.candidate_id == user.id, Application.job_id == job.job_id)
        )
        application = app_result.scalar_one_or_none()
        if application:
            return application, False, user_created or profile_created, refreshed
        application = Application(candidate_id=user.id, job_id=job.job_id)
        self.session.add(application)
        application.application_status = "IMPORTED"
        application.intake_source = "excel"
        application.intake_batch_id = batch_id
        await self.session.flush()
        return application, True, user_created or profile_created, refreshed

    @staticmethod
    def _profile_snapshot(profile: CandidateProfile) -> dict:
        fields = [
            "first_name", "last_name", "phone", "city", "state", "country",
            "current_company", "current_role", "total_experience", "expected_salary",
            "notice_period", "highest_education", "linkedin_url", "github_url",
            "portfolio_url", "source_type", "verification_status", "source_reference",
            "agent_processing_allowed", "talent_pool_status", "profile_freshness_status",
        ]
        return {field: getattr(profile, field) for field in fields}

    @staticmethod
    def _changed_fields(old: dict, new: dict) -> dict:
        return {
            key: {"old": old.get(key), "new": value}
            for key, value in new.items()
            if old.get(key) != value
        }

    @staticmethod
    def _change_summary(changed_fields: dict) -> str:
        if not changed_fields:
            return "No profile changes detected."
        labels = ", ".join(sorted(changed_fields)[:8])
        extra = len(changed_fields) - min(len(changed_fields), 8)
        suffix = f" and {extra} more" if extra else ""
        return f"Profile refreshed with updates to {labels}{suffix}."

    @staticmethod
    def _result_row(batch, requirement_id, candidate, evaluation) -> dict:
        scores = evaluation.scores
        return {
            "batch_id": batch.batch_id, "requirement_id": requirement_id,
            "job_id": evaluation.job_id, "application_id": evaluation.application_id,
            "candidate_id": evaluation.candidate_id, "email": candidate["email"],
            "candidate_name": f"{candidate.get('first_name') or ''} {candidate.get('last_name') or ''}".strip(),
            "current_role": candidate.get("current_role"), "experience_years": candidate.get("total_experience"),
            "decision": evaluation.decision, "queue_target": evaluation.queue_target,
            "final_score": scores.final_score, "skill_score": scores.skill_score,
            "experience_score": scores.experience_score, "education_score": scores.education_score,
            "certification_score": scores.certification_score, "keyword_score": scores.keyword_score,
            "explanation": evaluation.explanation, "source_type": candidate["source_type"],
            "verification_status": candidate["verification_status"],
            "source_reference": candidate.get("source_reference"),
            "evaluated_at": datetime.now(UTC).replace(tzinfo=None),
        }

    @staticmethod
    def _storage_path(path: Path) -> Path:
        resolved = path if path.is_absolute() else PROJECT_ROOT / path
        resolved = resolved.resolve()
        if STORAGE_ROOT.resolve() not in resolved.parents:
            raise HTTPException(status_code=400, detail="Excel intake files must be inside HireX/storage")
        return resolved


def requires_distribution_audit(result_rows: list[dict]) -> bool:
    return len(result_rows) >= 20 and not any(
        row["decision"] in {"PASS", "REVIEW"} for row in result_rows
    )


def _tokens(value: str | None) -> set[str]:
    return {
        token for token in re.split(r"[^a-z0-9+#.]+", (value or "").lower())
        if len(token) >= 2
    }


def _token_text(value: str | None) -> str:
    return " ".join(
        token for token in re.split(r"[^a-z0-9+#.]+", (value or "").lower())
        if len(token) >= 2
    )


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = _token_text(text)
    normalized_phrase = _token_text(phrase)
    return bool(normalized_phrase and normalized_phrase in normalized_text)


def _notice_days(value: str | None) -> int | None:
    if not value:
        return None
    lowered = value.lower()
    if "immediate" in lowered or "serving" in lowered:
        return 0
    match = re.search(r"(\d+)", lowered)
    return int(match.group(1)) if match else None


class CandidateFetchCriteria:
    """Pre-validator filter that simulates JD-driven sourcing eligibility."""

    def __init__(self, requirement: JobRequirementRow) -> None:
        self.requirement = requirement
        self.role_titles = [requirement.role, *requirement.role_title_variants]
        self.required_skill_tokens = [_tokens(skill) for skill in requirement.required_skills]
        self.location_tokens = _tokens(requirement.location)
        self.work_mode_tokens = _tokens(requirement.work_mode)
        self.domain_tokens = _tokens(requirement.preferred_industry_domain)

    def matches(self, candidate: CandidateIntakeRow, raw_text: str) -> bool:
        text = " ".join(
            str(value or "")
            for value in (
                candidate.current_role, candidate.current_company, candidate.city,
                candidate.state, candidate.country, candidate.highest_education,
                candidate.preferred_work_mode, candidate.preferred_locations,
                candidate.industry_domain,
                candidate.source_type, candidate.source_reference, raw_text,
            )
        )
        return all((
            self._role_matches(candidate.current_role, raw_text),
            self._skills_match(raw_text),
            self._experience_matches(candidate.total_experience),
            self._location_matches(candidate, raw_text),
            self._work_mode_matches(raw_text, candidate),
            self._salary_matches(candidate.expected_salary),
            self._notice_matches(candidate.notice_period),
            self._freshness_matches(candidate.source_reference, raw_text, candidate),
            self._domain_matches(text),
        ))

    def _role_matches(self, current_role: str | None, raw_text: str) -> bool:
        role_text = f"{current_role or ''} {raw_text}"
        return any(_contains_phrase(role_text, role) for role in self.role_titles if role)

    def _skills_match(self, raw_text: str) -> bool:
        if not self.required_skill_tokens:
            return True
        resume_tokens = _tokens(raw_text)
        matched = sum(1 for skill_tokens in self.required_skill_tokens if skill_tokens & resume_tokens)
        required_matches = max(1, round(len(self.required_skill_tokens) * 0.4))
        return matched >= required_matches

    def _experience_matches(self, years: float | None) -> bool:
        if years is None:
            return False
        if self.requirement.experience_min is not None and years < self.requirement.experience_min:
            return False
        if self.requirement.experience_max is not None and years > self.requirement.experience_max:
            return False
        return True

    def _location_matches(self, candidate: CandidateIntakeRow, raw_text: str) -> bool:
        if not self.location_tokens:
            return True
        if {"remote", "anywhere"} & self.location_tokens:
            return True
        location_text = " ".join(
            str(value or "") for value in (
                candidate.city, candidate.state, candidate.country,
                candidate.preferred_locations, raw_text,
            )
        )
        candidate_location_tokens = _tokens(location_text)
        if self.location_tokens & candidate_location_tokens:
            return True
        return bool(self.requirement.willing_to_relocate and candidate.willing_to_relocate is not False)

    def _work_mode_matches(self, raw_text: str, candidate: CandidateIntakeRow | None = None) -> bool:
        if not self.work_mode_tokens:
            return True
        if {"hybrid", "remote", "onsite", "on", "site"} & self.work_mode_tokens:
            candidate_mode = _tokens(candidate.preferred_work_mode if candidate else "")
            return not candidate_mode or bool(candidate_mode & self.work_mode_tokens)
        return bool(self.work_mode_tokens & _tokens(raw_text))

    def _salary_matches(self, expected_salary: int | None) -> bool:
        if expected_salary is None:
            return True
        if self.requirement.salary_max is not None and expected_salary > self.requirement.salary_max:
            return False
        return True

    def _notice_matches(self, notice_period: str | None) -> bool:
        if self.requirement.notice_period_max_days is None:
            return True
        days = _notice_days(notice_period)
        return days is None or days <= self.requirement.notice_period_max_days

    def _freshness_matches(self, source_reference: str | None, raw_text: str, candidate: CandidateIntakeRow | None = None) -> bool:
        if not candidate or not candidate.profile_last_updated_at:
            return True
        freshness_days = self.requirement.candidate_freshness_days or PROFILE_REFRESH_INTERVAL_DAYS
        cutoff = datetime.now(UTC) - timedelta(days=freshness_days)
        updated_at = candidate.profile_last_updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=UTC)
        return updated_at >= cutoff

    def _domain_matches(self, text: str) -> bool:
        if not self.domain_tokens:
            return True
        return bool(self.domain_tokens & _tokens(text))

    def source_rank(self, candidate) -> int:
        if not self.requirement.source_priority:
            return 0
        source_text = f"{getattr(candidate, 'source_type', '')} {getattr(candidate, 'source_reference', '')}"
        source_tokens = _tokens(source_text)
        for index, source in enumerate(self.requirement.source_priority):
            if _tokens(source) & source_tokens:
                return index
        return len(self.requirement.source_priority)
