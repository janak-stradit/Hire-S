"""Requirement scan service for job-detail readiness checks.

The HR job detail page calls this service before running a validator batch. It
checks the selected JD against the current PostgreSQL candidate pool and, when
configured, asks Amazon Bedrock for a second-pass recommendation. Bedrock is
optional so local development and demos still work without AWS credentials.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.settings import get_settings
from backend.excel_intake.contracts import JobRequirementRow
from backend.models.candidate import CandidateProfile
from backend.models.validator import ParsedResume


@dataclass
class RequirementScanResult:
    requirement_id: str
    role: str
    database_url: str
    total_candidates: int
    reusable_candidates: int
    fresh_candidates: int
    skill_match_candidates: int
    experience_match_candidates: int
    location_match_candidates: int
    estimated_reachable_candidates: int
    readiness_level: str
    findings: list[str]
    recommendations: list[str]
    bedrock_status: str
    bedrock_model_id: str | None
    bedrock_summary: str | None


class RequirementScanService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()

    async def scan(self, requirement: JobRequirementRow) -> dict:
        total_candidates = await self._count(select(func.count()).select_from(CandidateProfile))
        reusable_candidates = await self._count(
            select(func.count()).select_from(CandidateProfile).where(
                CandidateProfile.reusable_from_pool.is_(True),
                CandidateProfile.agent_processing_allowed.is_(True),
            )
        )
        fresh_candidates = await self._count(
            select(func.count()).select_from(CandidateProfile).where(
                CandidateProfile.reusable_from_pool.is_(True),
                CandidateProfile.agent_processing_allowed.is_(True),
                CandidateProfile.profile_freshness_status == "FRESH",
            )
        )
        skill_match_candidates = await self._matching_skill_count(requirement)
        experience_match_candidates = await self._matching_experience_count(requirement)
        location_match_candidates = await self._matching_location_count(requirement)
        estimated_reachable = min(
            value
            for value in [
                reusable_candidates,
                fresh_candidates or reusable_candidates,
                skill_match_candidates or reusable_candidates,
                experience_match_candidates or reusable_candidates,
                location_match_candidates or reusable_candidates,
            ]
            if value is not None
        )

        findings, recommendations, readiness = self._rule_based_findings(
            requirement=requirement,
            total_candidates=total_candidates,
            reusable_candidates=reusable_candidates,
            fresh_candidates=fresh_candidates,
            skill_match_candidates=skill_match_candidates,
            experience_match_candidates=experience_match_candidates,
            location_match_candidates=location_match_candidates,
            estimated_reachable=estimated_reachable,
        )
        bedrock_status, bedrock_summary = self._bedrock_summary(requirement, findings, recommendations)

        result = RequirementScanResult(
            requirement_id=requirement.requirement_id,
            role=requirement.role,
            database_url=self._masked_database_url(),
            total_candidates=total_candidates,
            reusable_candidates=reusable_candidates,
            fresh_candidates=fresh_candidates,
            skill_match_candidates=skill_match_candidates,
            experience_match_candidates=experience_match_candidates,
            location_match_candidates=location_match_candidates,
            estimated_reachable_candidates=estimated_reachable,
            readiness_level=readiness,
            findings=findings,
            recommendations=recommendations,
            bedrock_status=bedrock_status,
            bedrock_model_id=self.settings.bedrock_model_id if self.settings.bedrock_enabled else None,
            bedrock_summary=bedrock_summary,
        )
        return asdict(result)

    async def _count(self, statement) -> int:
        return int((await self.session.execute(statement)).scalar_one() or 0)

    async def _matching_skill_count(self, requirement: JobRequirementRow) -> int:
        skills = [skill.strip() for skill in requirement.required_skills if skill.strip()]
        if not skills:
            return 0
        predicates = []
        for skill in skills:
            pattern = f"%{skill}%"
            predicates.extend([ParsedResume.skills.ilike(pattern), ParsedResume.raw_text.ilike(pattern)])
        statement = (
            select(func.count(func.distinct(ParsedResume.candidate_id)))
            .join(CandidateProfile, CandidateProfile.candidate_id == ParsedResume.candidate_id)
            .where(
                CandidateProfile.reusable_from_pool.is_(True),
                CandidateProfile.agent_processing_allowed.is_(True),
                or_(*predicates),
            )
        )
        return await self._count(statement)

    async def _matching_experience_count(self, requirement: JobRequirementRow) -> int:
        statement = (
            select(func.count(func.distinct(ParsedResume.candidate_id)))
            .join(CandidateProfile, CandidateProfile.candidate_id == ParsedResume.candidate_id)
            .where(
                CandidateProfile.reusable_from_pool.is_(True),
                CandidateProfile.agent_processing_allowed.is_(True),
            )
        )
        if requirement.experience_min is not None:
            statement = statement.where(ParsedResume.total_experience_years >= requirement.experience_min)
        if requirement.experience_max is not None:
            statement = statement.where(ParsedResume.total_experience_years <= requirement.experience_max)
        return await self._count(statement)

    async def _matching_location_count(self, requirement: JobRequirementRow) -> int:
        location_terms = [
            term.strip()
            for term in requirement.location.replace("/", ",").replace("|", ",").split(",")
            if term.strip() and term.strip().lower() not in {"hybrid", "remote", "on-site", "onsite"}
        ]
        if not location_terms:
            return 0
        predicates = []
        for term in location_terms:
            pattern = f"%{term}%"
            predicates.extend(
                [
                    CandidateProfile.city.ilike(pattern),
                    CandidateProfile.state.ilike(pattern),
                    CandidateProfile.country.ilike(pattern),
                    CandidateProfile.source_reference.ilike(pattern),
                ]
            )
        statement = select(func.count()).select_from(CandidateProfile).where(
            CandidateProfile.reusable_from_pool.is_(True),
            CandidateProfile.agent_processing_allowed.is_(True),
            or_(*predicates),
        )
        return await self._count(statement)

    def _rule_based_findings(
        self,
        requirement: JobRequirementRow,
        total_candidates: int,
        reusable_candidates: int,
        fresh_candidates: int,
        skill_match_candidates: int,
        experience_match_candidates: int,
        location_match_candidates: int,
        estimated_reachable: int,
    ) -> tuple[list[str], list[str], str]:
        findings = [
            f"{total_candidates} candidate profiles are present in PostgreSQL.",
            f"{reusable_candidates} candidates are reusable for future openings.",
            f"{fresh_candidates} candidates are marked fresh for the current refresh cycle.",
            f"{skill_match_candidates} candidates match at least one required skill.",
            f"{experience_match_candidates} candidates fall inside the JD experience range.",
            f"{location_match_candidates} candidates match the JD location terms.",
        ]
        recommendations = []
        if not requirement.required_skills:
            recommendations.append("Add required skills before running validator scoring.")
        if skill_match_candidates < 25:
            recommendations.append("Skill reach is low; add role title variants or source more candidates.")
        if fresh_candidates < max(25, reusable_candidates * 0.4):
            recommendations.append("Run the 30-day freshness refresh before using this pool heavily.")
        if location_match_candidates == 0 and requirement.work_mode.lower() != "remote":
            recommendations.append("Location reach is low; confirm location terms or allow relocation.")
        if requirement.screening_review_score >= requirement.screening_pass_score:
            recommendations.append("Review threshold must stay below the pass threshold.")

        if estimated_reachable >= 100:
            readiness = "READY"
        elif estimated_reachable >= 25:
            readiness = "NEEDS_REVIEW"
        else:
            readiness = "LOW_REACH"
        return findings, recommendations or ["JD is ready for validator execution."], readiness

    def _bedrock_summary(
        self,
        requirement: JobRequirementRow,
        findings: list[str],
        recommendations: list[str],
    ) -> tuple[str, str | None]:
        if not self.settings.bedrock_enabled:
            return "disabled", None
        try:
            import boto3
        except ImportError:
            return "boto3_not_installed", None

        prompt = (
            "You are an HRTech requirement quality analyst. Review this job requirement scan "
            "and provide concise hiring operations recommendations.\n\n"
            f"Role: {requirement.role}\n"
            f"Required skills: {', '.join(requirement.required_skills)}\n"
            f"Preferred skills: {', '.join(requirement.preferred_skills)}\n"
            f"Location: {requirement.location}\n"
            f"Experience: {requirement.experience_min}-{requirement.experience_max} years\n"
            f"Findings: {json.dumps(findings)}\n"
            f"Rule recommendations: {json.dumps(recommendations)}"
        )
        try:
            client = boto3.client("bedrock-runtime", region_name=self.settings.aws_region)
            response = client.invoke_model(
                modelId=self.settings.bedrock_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(
                    {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 700,
                        "messages": [{"role": "user", "content": prompt}],
                    }
                ),
            )
            payload = json.loads(response["body"].read())
            content = payload.get("content", [])
            text = content[0].get("text") if content else None
            return "completed", text
        except Exception as exc:
            return f"failed: {exc}", None

    def _masked_database_url(self) -> str:
        parsed = urlsplit(self.settings.database_url)
        host = parsed.hostname or "localhost"
        port = f":{parsed.port}" if parsed.port else ""
        username = parsed.username or "user"
        netloc = f"{username}:***@{host}{port}"
        return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))
