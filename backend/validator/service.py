"""HireX pre-screen validator orchestration.

This service is the backbone of the screening flow. It converts an application
into parsed resume/JD records, calculates explainable component scores, applies
threshold policy, updates candidate/application state, and persists an auditable
`ValidatorResult` for HR and future agents.
"""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.validator import ValidatorResult
from backend.models.candidate import CandidateLifecycleEvent
from backend.repositories.validator_repository import ValidatorRepository
from backend.validator.contracts import (
    BulkEvaluateResponse,
    ScoreWeights,
    Thresholds,
    ValidatorEvaluation,
)
from backend.validator.decision_engine import make_decision
from backend.validator.errors import ValidatorInputError
from backend.validator.explanations import build_explanation
from backend.validator.resume_parser import (
    extract_text_from_path,
    parse_job_description_text,
    parse_resume_text,
)
from backend.validator.scoring import calculate_scores
from backend.validator.skill_matcher import match_skills

APPLICATION_STATUS_BY_DECISION = {
    "PASS": "R1_READY",
    "REVIEW": "UNDER_REVIEW",
    "FAIL": "REJECTED",
}

VALIDATOR_VERSION = "validator-2.4-intelligence"
PARSER_VERSION = "resume-parser-2.4"
SCORING_CONFIG_VERSION = "scoring-config-2.4"
DECISION_POLICY_VERSION = "threshold-policy-1.1"


class ValidatorService:
    """Run explainable candidate-to-JD validation for one or many applications."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ValidatorRepository(session)

    async def evaluate_application(
        self,
        application_id: str,
        weights: ScoreWeights | None = None,
        thresholds: Thresholds | None = None,
        resume_text_override: str | None = None,
        commit: bool = True,
    ) -> ValidatorEvaluation:
        """Evaluate one application and return the API-safe result contract."""
        try:
            result = await self._evaluate(application_id, weights, thresholds, resume_text_override)
        except ValidatorInputError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        if commit:
            await self.session.commit()
            await self.session.refresh(result)
        return self._to_contract(result)

    async def bulk_evaluate(
        self,
        application_ids: list[str],
        weights: ScoreWeights | None = None,
        thresholds: Thresholds | None = None,
    ) -> BulkEvaluateResponse:
        """Evaluate multiple applications with the exact same scoring policy."""
        results: list[ValidatorEvaluation] = []
        for application_id in application_ids:
            results.append(await self.evaluate_application(application_id, weights, thresholds))
        return BulkEvaluateResponse(
            total_requested=len(application_ids),
            evaluated=len(results),
            results=results,
        )

    async def get_result(self, validator_result_id: str) -> ValidatorEvaluation:
        result = await self.repository.get_result(validator_result_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validator result not found")
        return self._to_contract(result)

    async def get_latest_for_application(self, application_id: str) -> ValidatorEvaluation:
        result = await self.repository.get_latest_result_for_application(application_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validator result not found")
        return self._to_contract(result)

    async def list_queue(self, queue_target: str, job_id: str | None = None) -> list[ValidatorEvaluation]:
        """Expose candidates already routed to a downstream queue such as R1."""
        results = await self.repository.list_queue(queue_target, job_id)
        return [self._to_contract(result) for result in results]

    async def _evaluate(
        self,
        application_id: str,
        weights: ScoreWeights | None,
        thresholds: Thresholds | None,
        resume_text_override: str | None = None,
    ) -> ValidatorResult:
        """Internal scoring pipeline.

        The order is important:
        load application -> extract resume -> parse JD -> score -> decide ->
        update workflow state -> persist parsed artifacts -> persist result.
        """
        application = await self.repository.get_application(application_id)
        if not application:
            raise ValidatorInputError("Application not found")
        resume = await self.repository.latest_resume_for_candidate(application.candidate_id)
        if not resume:
            raise ValidatorInputError("Candidate must upload a resume before validation")
        if not application.job:
            raise ValidatorInputError("Application job is missing")

        # Excel intake provides already-extracted rich text for synthetic and
        # imported candidates. Direct application validation falls back to the
        # uploaded resume path.
        resume_text = resume_text_override if resume_text_override is not None else extract_text_from_path(resume.storage_path)
        if not resume_text.strip():
            raise ValidatorInputError("Resume text could not be extracted")
        parsed_resume_data = parse_resume_text(resume_text)
        profile = application.candidate
        # Candidate profile fields are merged back into parsed resume evidence so
        # profile updates/freshness refreshes can improve future validations even
        # if the original resume text was incomplete.
        if profile.highest_education:
            profile_education = parse_resume_text(profile.highest_education).education
            parsed_resume_data.education = list(dict.fromkeys(parsed_resume_data.education + profile_education))
        if profile.total_experience is not None:
            parsed_resume_data.total_experience_years = max(
                parsed_resume_data.total_experience_years, profile.total_experience
            )
        parsed_job_data = parse_job_description_text(
            description=application.job.description,
            skills_required=application.job.skills_required,
            experience_min=application.job.experience_min,
            experience_max=application.job.experience_max,
            preferred_skills=application.job.preferred_skills,
            education_requirements=application.job.education_requirements,
            certifications=application.job.mandatory_certifications,
        )
        scores = calculate_scores(parsed_resume_data, parsed_job_data, weights)
        skill_match = match_skills(
            parsed_resume_data.skills, parsed_job_data.required_skills, parsed_resume_data.raw_text
        )
        decision = make_decision(scores.final_score, thresholds)
        # Explanations and reason codes are stored with the result so HR can see
        # why a candidate was PASS, REVIEW, or FAIL without recalculating scores.
        explanation = build_explanation(
            scores, decision.decision, skill_match.matched_skills, skill_match.missing_skills
        )
        rejection_reason_codes = self._reason_codes(
            decision.decision,
            scores.skill_score,
            scores.experience_score,
            scores.education_score,
            scores.certification_score,
            scores.keyword_score,
            skill_match.missing_skills,
        )
        application.application_status = APPLICATION_STATUS_BY_DECISION[decision.decision]
        previous_pool_status = profile.talent_pool_status
        # FAIL returns a candidate to the reusable pool; PASS/REVIEW keeps the
        # person in-process for HR/R1 so the same candidate is not reused blindly.
        profile.talent_pool_status = "AVAILABLE" if decision.decision == "FAIL" else "IN_PROCESS"
        profile.reusable_from_pool = decision.decision == "FAIL" and profile.agent_processing_allowed
        profile.last_evaluated_at = datetime.now(UTC)
        profile.last_outcome = f"VALIDATOR_{decision.decision}"
        self.session.add(CandidateLifecycleEvent(
            candidate_id=application.candidate_id,
            application_id=application.application_id,
            event_type="VALIDATOR_DECISION",
            from_status=previous_pool_status,
            to_status=profile.talent_pool_status,
            reason=explanation,
            event_metadata={"decision": decision.decision, "score": scores.final_score},
        ))

        parsed_resume = await self.repository.create_parsed_resume(
            resume_id=resume.resume_id,
            candidate_id=application.candidate_id,
            skills=",".join(parsed_resume_data.skills),
            total_experience_years=parsed_resume_data.total_experience_years,
            education=",".join(parsed_resume_data.education),
            certifications=",".join(parsed_resume_data.certifications),
            projects="\n".join(parsed_resume_data.projects),
            sections=parsed_resume_data.sections,
            raw_text=parsed_resume_data.raw_text,
        )
        parsed_jd = await self.repository.create_parsed_job_description(
            job_id=application.job_id,
            required_skills=",".join(parsed_job_data.required_skills),
            preferred_skills=",".join(parsed_job_data.preferred_skills),
            experience_min=parsed_job_data.experience_min,
            experience_max=parsed_job_data.experience_max,
            education_requirements=",".join(parsed_job_data.education_requirements),
            certifications=",".join(parsed_job_data.certifications),
            raw_text=parsed_job_data.raw_text,
        )
        return await self.repository.create_result(
            application_id=application.application_id,
            candidate_id=application.candidate_id,
            job_id=application.job_id,
            intake_batch_id=application.intake_batch_id,
            parsed_resume_id=parsed_resume.parsed_resume_id,
            parsed_jd_id=parsed_jd.parsed_jd_id,
            skill_score=scores.skill_score,
            experience_score=scores.experience_score,
            education_score=scores.education_score,
            certification_score=scores.certification_score,
            keyword_score=scores.keyword_score,
            final_score=scores.final_score,
            decision=decision.decision,
            queue_target=decision.queue_target,
            matched_skills=skill_match.matched_skills,
            missing_skills=skill_match.missing_skills,
            skill_evidence=skill_match.evidence,
            validator_version=VALIDATOR_VERSION,
            parser_version=PARSER_VERSION,
            scoring_config_version=SCORING_CONFIG_VERSION,
            decision_policy_version=DECISION_POLICY_VERSION,
            rejection_reason_codes=rejection_reason_codes,
            scoring_metadata={
                "score_weights": (weights or ScoreWeights()).model_dump(),
                "thresholds": (thresholds or Thresholds()).model_dump(),
                "matched_required_skills_count": len(skill_match.matched_skills),
                "missing_required_skills_count": len(skill_match.missing_skills),
            },
            explanation=explanation,
        )

    @staticmethod
    def _reason_codes(
        decision: str,
        skill_score: float,
        experience_score: float,
        education_score: float,
        certification_score: float,
        keyword_score: float,
        missing_skills: list[str],
    ) -> list[str]:
        """Convert weak evidence into normalized reason-bank codes."""
        codes: list[str] = []
        if decision == "PASS":
            return codes
        if skill_score < 55 or missing_skills:
            codes.append("SKILL_GAP")
        if experience_score < 60:
            codes.append("EXPERIENCE_MISMATCH")
        if education_score < 60:
            codes.append("EDUCATION_MISMATCH")
        if certification_score < 60:
            codes.append("CERTIFICATION_GAP")
        if keyword_score < 45:
            codes.append("LOW_KEYWORD_RELEVANCE")
        if decision == "REVIEW" and not codes:
            codes.append("BORDERLINE_SCORE")
        return list(dict.fromkeys(codes))

    @staticmethod
    def _to_contract(result: ValidatorResult) -> ValidatorEvaluation:
        """Map ORM result rows to the response model used by API/frontend/agents."""
        return ValidatorEvaluation(
            validator_result_id=result.validator_result_id,
            application_id=result.application_id,
            candidate_id=result.candidate_id,
            job_id=result.job_id,
            parsed_resume_id=result.parsed_resume_id,
            parsed_jd_id=result.parsed_jd_id,
            scores={
                "skill_score": result.skill_score,
                "experience_score": result.experience_score,
                "education_score": result.education_score,
                "certification_score": result.certification_score,
                "keyword_score": result.keyword_score,
                "final_score": result.final_score,
            },
            decision=result.decision,
            queue_target=result.queue_target,
            matched_skills=result.matched_skills,
            missing_skills=result.missing_skills,
            skill_evidence=result.skill_evidence,
            explanation=result.explanation,
        )
