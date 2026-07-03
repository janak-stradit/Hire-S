"""Read model and HR decision service for the operations dashboard.

This service translates normalized database records into dashboard-friendly
responses. It intentionally separates batch-level views from all-time pool
analytics so HR can review a specific hiring run without mixing counts from
previous roles.
"""

from fastapi import HTTPException
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from backend.models.application import Application
from backend.models.candidate import (
    CandidateBatchMembership,
    CandidateLifecycleEvent,
    CandidateProfile,
    CandidateRefreshChange,
    SourcingBatch,
)
from backend.models.hr_review import HRReviewAction
from backend.models.job import Job
from backend.models.resume import Resume
from backend.models.user import User
from backend.models.validator import ExcelIntakeBatch, ParsedResume, ValidatorResult
from backend.schemas.admin import ReviewActionRequest
from backend.services.batch_tracking_service import BatchTrackingService

ACTION_STATUSES = {
    "MOVE_FORWARD": "R1_READY",
    "HOLD": "ON_HOLD",
    "REJECT": "REJECTED",
}

REASON_BANK = [
    {"code": "SKILL_GAP", "label": "Skill gap", "description": "Required skills are missing or weak."},
    {"code": "EXPERIENCE_MISMATCH", "label": "Experience mismatch", "description": "Experience does not match the JD band."},
    {"code": "EDUCATION_MISMATCH", "label": "Education mismatch", "description": "Education evidence is below the requirement."},
    {"code": "CERTIFICATION_GAP", "label": "Certification gap", "description": "Required or useful certifications are missing."},
    {"code": "LOW_KEYWORD_RELEVANCE", "label": "Low keyword relevance", "description": "Resume language has low JD alignment."},
    {"code": "BORDERLINE_SCORE", "label": "Borderline score", "description": "Candidate is near the review threshold."},
    {"code": "LOCATION_MISMATCH", "label": "Location mismatch", "description": "Candidate location does not align with the role."},
    {"code": "COMPENSATION_MISMATCH", "label": "Compensation mismatch", "description": "Expected compensation may not fit the role."},
    {"code": "REFRESH_REQUIRED", "label": "Refresh required", "description": "Profile is stale and needs updated sourcing evidence."},
    {"code": "NOT_ROLE_ALIGNED", "label": "Not role aligned", "description": "HR or interviewer found a role alignment gap."},
]


class AdminDashboardService:
    """Aggregate validator evidence, HR actions, pool analytics, and timelines."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _latest_results(self, batch_id: str | None = None):
        """Select latest completed validator result per application.

        Failed/running/audit batches are excluded from normal HR lists so a
        partially interrupted run cannot influence hiring decisions.
        """
        latest_statement = (
            select(
                ValidatorResult.application_id,
                func.max(ValidatorResult.evaluated_at).label("evaluated_at"),
            )
            .outerjoin(
                ExcelIntakeBatch,
                ExcelIntakeBatch.batch_id == ValidatorResult.intake_batch_id,
            )
            .where(
                or_(
                    ValidatorResult.intake_batch_id.is_(None),
                    ExcelIntakeBatch.status == "COMPLETED",
                )
            )
            .group_by(ValidatorResult.application_id)
        )
        if batch_id:
            latest_statement = latest_statement.where(ValidatorResult.intake_batch_id == batch_id)
        return latest_statement.subquery()

    async def list_candidates(
        self,
        job_id: str | None,
        batch_id: str | None,
        decision: str | None,
        hr_action: str | None,
        workflow_state: str | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> dict:
        """Return the candidate table rows for the active HR filters.

        The frontend uses this endpoint for All, HR review, R1 shortlist, Held,
        Rejected, search, pagination, and selected-batch views.
        """
        latest_result = self._latest_results(batch_id)
        action = aliased(HRReviewAction)
        statement = (
            select(Application, ValidatorResult, CandidateProfile, User, Job, action)
            .join(ValidatorResult, ValidatorResult.application_id == Application.application_id)
            .join(
                latest_result,
                (latest_result.c.application_id == ValidatorResult.application_id)
                & (latest_result.c.evaluated_at == ValidatorResult.evaluated_at),
            )
            .join(CandidateProfile, CandidateProfile.candidate_id == Application.candidate_id)
            .join(User, User.id == CandidateProfile.candidate_id)
            .join(Job, Job.job_id == Application.job_id)
            .outerjoin(
                ExcelIntakeBatch,
                ExcelIntakeBatch.batch_id == ValidatorResult.intake_batch_id,
            )
            .outerjoin(
                action,
                action.validator_result_id == ValidatorResult.validator_result_id,
            )
        )
        statement = statement.where(
            or_(
                ValidatorResult.intake_batch_id.is_(None),
                ExcelIntakeBatch.status == "COMPLETED",
            )
        )
        if job_id:
            statement = statement.where(Application.job_id == job_id)
        if batch_id:
            statement = statement.where(ValidatorResult.intake_batch_id == batch_id)
        if decision:
            statement = statement.where(ValidatorResult.decision == decision)
        if hr_action:
            statement = statement.where(action.action == hr_action)
        if workflow_state == "PENDING":
            # PENDING means validator REVIEW candidates that still need a human
            # decision. PASS and FAIL are automatically routed by thresholds.
            statement = statement.where(
                ValidatorResult.decision == "REVIEW", action.action.is_(None)
            )
        elif workflow_state == "MOVE_FORWARD":
            statement = statement.where(
                or_(ValidatorResult.decision == "PASS", action.action == "MOVE_FORWARD")
            )
        elif workflow_state == "REJECT":
            statement = statement.where(
                or_(ValidatorResult.decision == "FAIL", action.action == "REJECT")
            )
        elif workflow_state == "HOLD":
            statement = statement.where(action.action == "HOLD")
        if search:
            term = f"%{search.strip().lower()}%"
            statement = statement.where(
                or_(
                    func.lower(User.email).like(term),
                    func.lower(CandidateProfile.first_name).like(term),
                    func.lower(CandidateProfile.last_name).like(term),
                    func.lower(CandidateProfile.first_name + ' ' + CandidateProfile.last_name).like(term),
                    func.lower(CandidateProfile.current_role).like(term),
                )
            )
        rows = (await self.session.execute(statement.order_by(ValidatorResult.final_score.desc()))).all()
        items = [self._candidate_row(*row) for row in rows]
        return {"items": items[offset : offset + limit], "total": len(items), "limit": limit, "offset": offset}

    async def summary(self, job_id: str | None, batch_id: str | None = None) -> dict[str, int]:
        """Compute dashboard cards for either one batch or the aggregate view."""
        result = await self.list_candidates(job_id, batch_id, None, None, None, None, 100000, 0)
        items = result["items"]
        return {
            "total": len(items),
            "pass_count": sum(item["validator_decision"] == "PASS" for item in items),
            "review_count": sum(item["validator_decision"] == "REVIEW" for item in items),
            "fail_count": sum(item["validator_decision"] == "FAIL" for item in items),
            "moved_forward": sum(
                item["validator_decision"] == "PASS" or item["hr_action"] == "MOVE_FORWARD"
                for item in items
            ),
            "held": sum(item["hr_action"] == "HOLD" for item in items),
            "rejected_by_hr": sum(item["hr_action"] == "REJECT" for item in items),
        }

    async def detail(self, application_id: str, validator_result_id: str | None = None) -> dict:
        """Build the candidate drawer payload.

        This joins validator scores, parsed resume sections, resume raw text,
        lifecycle timeline, freshness changes, HR review history, and version
        metadata so HR can audit the full reason behind a decision.
        """
        selected_result = (
            await self.session.get(ValidatorResult, validator_result_id)
            if validator_result_id
            else None
        )
        if selected_result and selected_result.application_id != application_id:
            raise HTTPException(status_code=404, detail="Evaluation does not belong to this application")
        listing = await self.list_candidates(
            None,
            selected_result.intake_batch_id if selected_result else None,
            None, None, None, None, 100000, 0,
        )
        row = next(
            (
                item for item in listing["items"]
                if item["application_id"] == application_id
                and (not validator_result_id or item["validator_result_id"] == validator_result_id)
            ),
            None,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Evaluated application not found")
        result = await self.session.get(ValidatorResult, row["validator_result_id"])
        parsed = await self.session.get(ParsedResume, result.parsed_resume_id)
        profile = await self.session.get(CandidateProfile, result.candidate_id)
        job = await self.session.get(Job, result.job_id)
        resume = (
            await self.session.execute(
                select(Resume).where(Resume.candidate_id == result.candidate_id).order_by(Resume.uploaded_at.desc())
            )
        ).scalars().first()
        history_rows = (
            await self.session.execute(
                select(HRReviewAction, User)
                .join(User, User.id == HRReviewAction.actor_id)
                .where(HRReviewAction.application_id == application_id)
                .order_by(HRReviewAction.created_at.desc())
            )
        ).all()
        timeline_rows = (
            await self.session.execute(
                select(CandidateLifecycleEvent)
                .where(CandidateLifecycleEvent.candidate_id == result.candidate_id)
                .order_by(CandidateLifecycleEvent.created_at.desc())
                .limit(20)
            )
        ).scalars().all()
        refresh_rows = (
            await self.session.execute(
                select(CandidateRefreshChange)
                .where(CandidateRefreshChange.candidate_id == result.candidate_id)
                .order_by(CandidateRefreshChange.created_at.desc())
                .limit(10)
            )
        ).scalars().all()
        row.update(
            phone=profile.phone,
            current_company=profile.current_company,
            education=parsed.sections.get("education", parsed.education),
            skills=[value.strip() for value in parsed.skills.split(",") if value.strip()],
            certifications=parsed.sections.get("certifications", parsed.certifications),
            projects=parsed.sections.get("projects", parsed.projects),
            resume_sections=parsed.sections,
            matched_skills=result.matched_skills,
            missing_skills=result.missing_skills,
            skill_evidence=result.skill_evidence,
            resume_text=parsed.raw_text,
            resume_filename=resume.original_filename if resume else None,
            source_reference=profile.source_reference,
            explanation=result.explanation,
            scores={
                "skills": result.skill_score,
                "experience": result.experience_score,
                "education": result.education_score,
                "certifications": result.certification_score,
                "keywords": result.keyword_score,
                "final": result.final_score,
            },
            pass_threshold=job.screening_pass_score,
            review_threshold=job.screening_review_score,
            education_requirement=job.education_requirements or "",
            required_certifications=[
                value.strip() for value in (job.mandatory_certifications or "").split(",") if value.strip()
            ],
            candidate_timeline=[
                {
                    "event_id": item.event_id,
                    "event_type": item.event_type,
                    "from_status": item.from_status,
                    "to_status": item.to_status,
                    "reason": item.reason,
                    "metadata": item.event_metadata,
                    "created_at": item.created_at,
                }
                for item in timeline_rows
            ],
            refresh_changes=[
                {
                    "refresh_change_id": item.refresh_change_id,
                    "changed_fields": item.changed_fields,
                    "change_summary": item.change_summary,
                    "created_at": item.created_at,
                }
                for item in refresh_rows
            ],
            validator_versions={
                "validator_version": result.validator_version,
                "parser_version": result.parser_version,
                "scoring_config_version": result.scoring_config_version,
                "decision_policy_version": result.decision_policy_version,
                "scoring_version": result.scoring_version,
            },
            rejection_reason_codes=result.rejection_reason_codes,
            review_history=[
                {
                    "action_id": review.action_id,
                    "action": review.action,
                    "reason": review.reason,
                    "reason_codes": review.reason_codes,
                    "actor_email": actor.email,
                    "created_at": review.created_at,
                }
                for review, actor in history_rows
            ],
        )
        return row

    async def review(self, application_id: str, payload: ReviewActionRequest, actor: User) -> dict:
        """Persist HR's decision for a REVIEW-band candidate.

        PASS candidates are already shortlisted for R1 and FAIL candidates are
        already rejected by the validator. This method is reserved for the
        middle band where human judgment is required.
        """
        detail = await self.detail(application_id, payload.validator_result_id)
        if detail["validator_decision"] != "REVIEW":
            raise HTTPException(
                status_code=409,
                detail="HR action is only allowed for candidates in the REVIEW threshold band",
            )
        if detail["hr_action"] is not None:
            raise HTTPException(status_code=409, detail="This candidate already has a final HR decision")
        application = await self.session.get(Application, application_id)
        action = HRReviewAction(
            application_id=application_id,
            validator_result_id=detail["validator_result_id"],
            action=payload.action,
            reason=payload.reason.strip(),
            reason_codes=payload.reason_codes,
            actor_id=actor.id,
        )
        application.application_status = ACTION_STATUSES[payload.action]
        self.session.add(action)
        # If this candidate came from an intake batch, update the batch
        # membership as well so the Batches screen and candidate master timeline
        # stay in sync with the HR action.
        membership = await self.session.scalar(
            select(CandidateBatchMembership).where(
                CandidateBatchMembership.validator_result_id == detail["validator_result_id"]
            )
        )
        if membership:
            await BatchTrackingService(self.session).record_stage_decision(
                membership.membership_id,
                "HR_REVIEW",
                {"MOVE_FORWARD": "ADVANCE", "HOLD": "HOLD", "REJECT": "REJECT"}[payload.action],
                payload.reason,
                actor,
            )
        else:
            await self.session.commit()
        await self.session.refresh(action)
        return {
            "action_id": action.action_id,
            "application_id": application_id,
            "action": action.action,
            "application_status": application.application_status,
            "created_at": action.created_at,
        }

    async def pool_analytics(self) -> dict:
        """Return all-time reusable-pool health metrics.

        This is intentionally separate from batch dashboards: it answers how the
        overall talent database is growing, why people are rejected, and which
        sources contribute candidates.
        """
        status_rows = (await self.session.execute(
            select(CandidateProfile.talent_pool_status, func.count())
            .group_by(CandidateProfile.talent_pool_status)
        )).all()
        source_rows = (await self.session.execute(
            select(CandidateProfile.source_type, func.count())
            .group_by(CandidateProfile.source_type)
        )).all()
        reason_rows = (await self.session.execute(
            select(ValidatorResult.decision, ValidatorResult.rejection_reason_codes)
        )).all()
        reason_counts: dict[str, int] = {}
        for decision, codes in reason_rows:
            if decision == "PASS":
                continue
            for code in codes or []:
                reason_counts[code] = reason_counts.get(code, 0) + 1
        batch_rows = (await self.session.execute(
            select(
                ValidatorResult.intake_batch_id,
                func.count(),
                func.sum(case((ValidatorResult.decision == "PASS", 1), else_=0)),
                func.sum(case((ValidatorResult.decision == "REVIEW", 1), else_=0)),
                func.sum(case((ValidatorResult.decision == "FAIL", 1), else_=0)),
            )
            .where(ValidatorResult.intake_batch_id.is_not(None))
            .group_by(ValidatorResult.intake_batch_id)
            .limit(20)
        )).all()
        return {
            "pool_status": {status: count for status, count in status_rows},
            "source_mix": {source: count for source, count in source_rows},
            "reason_counts": dict(sorted(reason_counts.items(), key=lambda item: item[1], reverse=True)),
            "batch_outcomes": [
                {
                    "batch_id": batch_id,
                    "evaluated": int(total or 0),
                    "pass_count": int(pass_count or 0),
                    "review_count": int(review_count or 0),
                    "fail_count": int(fail_count or 0),
                }
                for batch_id, total, pass_count, review_count, fail_count in batch_rows
            ],
        }

    async def sourcing_batches(self) -> list[dict]:
        """List recent source imports for audit and future connector tracking."""
        rows = list((await self.session.scalars(
            select(SourcingBatch).order_by(SourcingBatch.created_at.desc()).limit(100)
        )).all())
        return [
            {
                "sourcing_batch_id": item.sourcing_batch_id,
                "source_type": item.source_type,
                "source_reference": item.source_reference,
                "source_label": item.source_label,
                "status": item.status,
                "total_candidates": item.total_candidates,
                "known_candidates": item.known_candidates,
                "new_candidates": item.new_candidates,
                "refreshed_candidates": item.refreshed_candidates,
                "metadata": item.metadata_json,
                "created_at": item.created_at,
            }
            for item in rows
        ]

    @staticmethod
    def reason_bank() -> list[dict]:
        """Expose normalized reason codes used by validator and HR decisions."""
        return REASON_BANK

    @staticmethod
    def _candidate_row(application, result, profile, user, job, action) -> dict:
        """Flatten joined ORM rows into one table row for the frontend."""
        name = " ".join(value for value in (profile.first_name, profile.last_name) if value).strip()
        location = ", ".join(value for value in (profile.city, profile.state, profile.country) if value)
        return {
            "application_id": application.application_id,
            "validator_result_id": result.validator_result_id,
            "candidate_id": profile.candidate_id,
            "name": name or user.email.split("@", 1)[0],
            "email": user.email,
            "current_role": profile.current_role,
            "location": location,
            "experience_years": profile.total_experience or 0,
            "job_id": job.job_id,
            "job_title": job.title,
            "final_score": result.final_score,
            "validator_decision": result.decision,
            "queue_target": result.queue_target,
            "application_status": application.application_status,
            "hr_action": action.action if action else None,
            "source_type": profile.source_type,
            "verification_status": profile.verification_status,
            "evaluated_at": result.evaluated_at,
        }

    async def global_search(self, query: str) -> dict:
        """Global command palette search across candidates and active jobs."""
        if not query or len(query.strip()) < 2:
            return {"candidates": [], "jobs": []}
            
        term = f"%{query.strip().lower()}%"
        
        # Search candidates (limit 5)
        candidate_stmt = (
            select(CandidateProfile, User)
            .join(User, User.id == CandidateProfile.candidate_id)
            .where(
                or_(
                    func.lower(User.email).like(term),
                    func.lower(CandidateProfile.first_name).like(term),
                    func.lower(CandidateProfile.last_name).like(term),
                    func.lower(CandidateProfile.first_name + ' ' + CandidateProfile.last_name).like(term),
                    func.lower(CandidateProfile.current_role).like(term),
                )
            )
            .limit(5)
        )
        cand_rows = (await self.session.execute(candidate_stmt)).all()
        candidates = []
        for profile, user in cand_rows:
            name = " ".join(value for value in (profile.first_name, profile.last_name) if value).strip()
            candidates.append({
                "id": profile.candidate_id,
                "email": user.email,
                "name": name or user.email.split("@", 1)[0],
                "role": profile.current_role or "Candidate",
            })
            
        # Search jobs (limit 5)
        job_stmt = (
            select(Job)
            .where(
                or_(
                    func.lower(Job.title).like(term),
                    func.lower(Job.department).like(term),
                    func.lower(Job.requirement_id).like(term),
                )
            )
            .limit(5)
        )
        job_rows = (await self.session.scalars(job_stmt)).all()
        jobs = []
        for job in job_rows:
            jobs.append({
                "id": job.requirement_id,
                "title": job.title,
                "department": job.department,
                "status": job.status,
            })
            
        return {"candidates": candidates, "jobs": jobs}
