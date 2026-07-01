"""Batch membership and stage transition tracking.

Validator results answer "how did this candidate score?" Batch memberships answer
"where is this candidate inside this hiring run?" Keeping those separate lets the
same candidate appear in multiple job batches without duplicating the master
candidate profile.
"""

from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.candidate import (
    CandidateBatchMembership,
    CandidateLifecycleEvent,
    CandidateProfile,
    CandidateStageEvent,
)
from backend.models.user import User

STATUS_BY_VALIDATOR_DECISION = {
    "PASS": ("R1", "R1_READY"),
    "REVIEW": ("HR_REVIEW", "HR_REVIEW"),
    "FAIL": ("COMPLETE", "REJECTED"),
}

ACTIVE_MEMBERSHIP_STATUSES = {
    "HR_REVIEW", "R1_READY", "T1_READY", "T2_READY", "MANAGERIAL_READY",
    "FINAL_HR_READY", "HELD",
}


async def track_validator_result(
    session: AsyncSession,
    *,
    batch_id: str,
    application_id: str,
    candidate_id: str,
    job_id: str,
    validator_result_id: str,
    decision: str,
    final_score: float,
    source_kind: str,
) -> CandidateBatchMembership:
    """Create or update the candidate's status inside one validator batch."""
    stage, workflow_status = STATUS_BY_VALIDATOR_DECISION[decision]
    membership = await session.scalar(
        select(CandidateBatchMembership).where(
            CandidateBatchMembership.batch_id == batch_id,
            CandidateBatchMembership.candidate_id == candidate_id,
        )
    )
    if not membership:
        membership = CandidateBatchMembership(
            batch_id=batch_id,
            application_id=application_id,
            candidate_id=candidate_id,
            job_id=job_id,
            source_kind=source_kind,
            validator_result_id=validator_result_id,
            validator_decision=decision,
            final_score=final_score,
            current_stage=stage,
            workflow_status=workflow_status,
        )
        session.add(membership)
    else:
        membership.validator_result_id = validator_result_id
        membership.validator_decision = decision
        membership.final_score = final_score
        membership.current_stage = stage
        membership.workflow_status = workflow_status
        membership.updated_at = datetime.now(UTC)
    return membership


class BatchTrackingService:
    """Manage post-validator movement through HR/R1/T1/T2 style stages."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_memberships(self, batch_id: str) -> list[dict]:
        """Return candidates for a selected batch in score order."""
        memberships = list((await self.session.scalars(
            select(CandidateBatchMembership)
            .where(CandidateBatchMembership.batch_id == batch_id)
            .order_by(CandidateBatchMembership.final_score.desc())
        )).all())
        return [
            {
                "membership_id": item.membership_id,
                "batch_id": item.batch_id,
                "candidate_id": item.candidate_id,
                "application_id": item.application_id,
                "job_id": item.job_id,
                "validator_result_id": item.validator_result_id,
                "source_kind": item.source_kind,
                "validator_decision": item.validator_decision,
                "final_score": item.final_score,
                "current_stage": item.current_stage,
                "workflow_status": item.workflow_status,
            }
            for item in memberships
        ]

    async def record_stage_decision(
        self,
        membership_id: str,
        stage: str,
        decision: str,
        reason: str,
        actor: User,
    ) -> dict:
        """Record a human or agent decision and move the membership forward."""
        membership = await self.session.get(CandidateBatchMembership, membership_id)
        if not membership:
            raise HTTPException(status_code=404, detail="Candidate batch membership not found")
        if membership.workflow_status in {"REJECTED", "HIRED"}:
            raise HTTPException(status_code=409, detail="This batch candidate already has a terminal outcome")

        if decision == "REJECT":
            # Terminal decisions close the batch membership and may return the
            # candidate to the reusable pool after all active memberships finish.
            next_status, next_stage = "REJECTED", "COMPLETE"
        elif decision == "HOLD":
            next_status, next_stage = "HELD", stage
        elif decision == "HIRED":
            next_status, next_stage = "HIRED", "COMPLETE"
        else:
            next_status = {
                "HR_REVIEW": "R1_READY",
                "R1": "T1_READY",
                "T1": "T2_READY",
                "T2": "MANAGERIAL_READY",
                "MANAGERIAL": "FINAL_HR_READY",
                "FINAL_HR": "HIRED",
            }[stage]
            next_stage = {
                "HR_REVIEW": "R1",
                "R1": "T1",
                "T1": "T2",
                "T2": "MANAGERIAL",
                "MANAGERIAL": "FINAL_HR",
                "FINAL_HR": "COMPLETE",
            }[stage]

        membership.current_stage = next_stage
        membership.workflow_status = next_status
        membership.updated_at = datetime.now(UTC)
        self.session.add(CandidateStageEvent(
            membership_id=membership.membership_id,
            candidate_id=membership.candidate_id,
            application_id=membership.application_id,
            batch_id=membership.batch_id,
            stage=stage,
            decision=decision,
            reason=reason.strip(),
            actor_id=actor.id,
        ))
        await self._refresh_candidate_status(membership.candidate_id, reason, membership.application_id)
        await self.session.commit()
        return {
            "membership_id": membership.membership_id,
            "candidate_id": membership.candidate_id,
            "batch_id": membership.batch_id,
            "current_stage": membership.current_stage,
            "workflow_status": membership.workflow_status,
        }

    async def _refresh_candidate_status(
        self, candidate_id: str, reason: str, application_id: str
    ) -> None:
        """Recalculate the candidate-level pool status from all memberships."""
        profile = await self.session.get(CandidateProfile, candidate_id)
        hired = await self.session.scalar(
            select(func.count()).select_from(CandidateBatchMembership).where(
                CandidateBatchMembership.candidate_id == candidate_id,
                CandidateBatchMembership.workflow_status == "HIRED",
            )
        )
        active = await self.session.scalar(
            select(func.count()).select_from(CandidateBatchMembership).where(
                CandidateBatchMembership.candidate_id == candidate_id,
                CandidateBatchMembership.workflow_status.in_(ACTIVE_MEMBERSHIP_STATUSES),
            )
        )
        previous = profile.talent_pool_status
        if hired:
            profile.talent_pool_status = "HIRED"
            profile.reusable_from_pool = False
            profile.last_outcome = "HIRED"
        elif active:
            profile.talent_pool_status = "IN_PROCESS"
            profile.reusable_from_pool = False
            profile.last_outcome = "IN_PROCESS"
        else:
            profile.talent_pool_status = "AVAILABLE"
            profile.reusable_from_pool = profile.agent_processing_allowed
            profile.last_outcome = "RETURNED_TO_POOL"
        self.session.add(CandidateLifecycleEvent(
            candidate_id=candidate_id,
            application_id=application_id,
            event_type="STAGE_DECISION",
            from_status=previous,
            to_status=profile.talent_pool_status,
            reason=reason.strip(),
            event_metadata={"active_batch_memberships": int(active or 0)},
        ))
