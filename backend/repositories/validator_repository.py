import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.application import Application
from backend.models.resume import Resume
from backend.models.candidate import CandidateProfile
from backend.models.validator import ParsedJobDescription, ParsedResume, ValidatorResult


class ValidatorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_application(self, application_id: str) -> Application | None:
        result = await self.session.execute(
            select(Application)
            .where(Application.application_id == application_id)
            .options(selectinload(Application.job), selectinload(Application.candidate))
        )
        return result.scalar_one_or_none()

    async def latest_resume_for_candidate(self, candidate_id: str) -> Resume | None:
        result = await self.session.execute(
            select(Resume)
            .where(Resume.candidate_id == candidate_id)
            .order_by(Resume.uploaded_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_parsed_resume(
        self,
        *,
        resume_id: str,
        candidate_id: str,
        skills: str,
        total_experience_years: float,
        education: str,
        certifications: str,
        projects: str,
        sections: dict[str, str],
        raw_text: str,
    ) -> ParsedResume:
        parsed = ParsedResume(
            resume_id=resume_id,
            candidate_id=candidate_id,
            skills=skills,
            total_experience_years=total_experience_years,
            education=education,
            certifications=certifications,
            projects=projects,
            sections=sections,
            raw_text=raw_text,
        )
        self.session.add(parsed)
        await self.session.flush()
        return parsed

    async def create_parsed_job_description(
        self,
        *,
        job_id: str,
        required_skills: str,
        preferred_skills: str,
        experience_min: int | None,
        experience_max: int | None,
        education_requirements: str,
        certifications: str,
        raw_text: str,
    ) -> ParsedJobDescription:
        parsed = ParsedJobDescription(
            job_id=job_id,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            experience_min=experience_min,
            experience_max=experience_max,
            education_requirements=education_requirements,
            certifications=certifications,
            raw_text=raw_text,
        )
        self.session.add(parsed)
        await self.session.flush()
        return parsed

    async def create_result(
        self,
        *,
        application_id: str,
        candidate_id: str,
        job_id: str,
        intake_batch_id: str | None,
        parsed_resume_id: str,
        parsed_jd_id: str,
        skill_score: float,
        experience_score: float,
        education_score: float,
        certification_score: float,
        keyword_score: float,
        final_score: float,
        decision: str,
        queue_target: str,
        matched_skills: list[str],
        missing_skills: list[str],
        skill_evidence: dict[str, list[str]],
        validator_version: str,
        parser_version: str,
        scoring_config_version: str,
        decision_policy_version: str,
        rejection_reason_codes: list[str],
        scoring_metadata: dict,
        explanation: str,
    ) -> ValidatorResult:
        result = ValidatorResult(
            application_id=application_id,
            candidate_id=candidate_id,
            job_id=job_id,
            intake_batch_id=intake_batch_id,
            parsed_resume_id=parsed_resume_id,
            parsed_jd_id=parsed_jd_id,
            skill_score=skill_score,
            experience_score=experience_score,
            education_score=education_score,
            certification_score=certification_score,
            keyword_score=keyword_score,
            final_score=final_score,
            decision=decision,
            queue_target=queue_target,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            skill_evidence=skill_evidence,
            validator_version=validator_version,
            parser_version=parser_version,
            scoring_config_version=scoring_config_version,
            decision_policy_version=decision_policy_version,
            rejection_reason_codes=rejection_reason_codes,
            scoring_metadata=scoring_metadata,
            explanation=explanation,
        )
        self.session.add(result)
        await self.session.flush()
        return result

    async def get_result(self, validator_result_id: str) -> ValidatorResult | None:
        return await self.session.get(ValidatorResult, validator_result_id)

    async def get_latest_result_for_application(self, application_id: str) -> ValidatorResult | None:
        result = await self.session.execute(
            select(ValidatorResult)
            .where(ValidatorResult.application_id == application_id)
            .order_by(ValidatorResult.evaluated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_queue(self, queue_target: str, job_id: str | None = None) -> list[ValidatorResult]:
        latest_ids = (
            select(ValidatorResult.application_id, sa.func.max(ValidatorResult.evaluated_at).label("latest"))
            .group_by(ValidatorResult.application_id)
            .subquery()
        )
        query = (
            select(ValidatorResult)
            .join(latest_ids, sa.and_(
                ValidatorResult.application_id == latest_ids.c.application_id,
                ValidatorResult.evaluated_at == latest_ids.c.latest,
            ))
            .join(CandidateProfile, CandidateProfile.candidate_id == ValidatorResult.candidate_id)
            .where(
                ValidatorResult.queue_target == queue_target,
                CandidateProfile.agent_processing_allowed.is_(True),
            )
            .order_by(ValidatorResult.final_score.desc())
        )
        if job_id:
            query = query.where(ValidatorResult.job_id == job_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
