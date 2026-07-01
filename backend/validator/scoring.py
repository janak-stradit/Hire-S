from backend.validator.contracts import (
    ParsedJobDescriptionData,
    ParsedResumeData,
    ScoreBreakdown,
    ScoreWeights,
)
from backend.validator.education_matcher import education_match_score
from backend.validator.experience_matcher import experience_match_score
from backend.validator.keyword_matcher import keyword_relevance_score
from backend.validator.skill_matcher import skill_match_score
from backend.validator.skill_matcher import match_skills


def certification_match_score(candidate_certs: list[str], required_certs: list[str]) -> float:
    if not required_certs:
        return 100.0
    if not candidate_certs:
        return 0.0
    matched = len(set(candidate_certs).intersection(required_certs))
    return round((matched / len(set(required_certs))) * 100, 2)


def calculate_scores(
    resume: ParsedResumeData,
    job: ParsedJobDescriptionData,
    weights: ScoreWeights | None = None,
) -> ScoreBreakdown:
    normalized_weights = (weights or ScoreWeights()).normalized()
    skill_score = match_skills(resume.skills, job.required_skills, resume.raw_text).score
    experience_score = experience_match_score(
        resume.total_experience_years, job.experience_min, job.experience_max
    )
    education_score = education_match_score(resume.education, job.education_requirements)
    cert_score = certification_match_score(resume.certifications, job.certifications)
    keyword_score = keyword_relevance_score(
        resume.raw_text,
        job.raw_text,
        resume.skills,
        job.required_skills + job.preferred_skills,
    )
    components = {
        "skills": (skill_score, normalized_weights.skills, True),
        "experience": (experience_score, normalized_weights.experience, True),
        "education": (education_score, normalized_weights.education, bool(job.education_requirements)),
        "certifications": (cert_score, normalized_weights.certifications, bool(job.certifications)),
        "keywords": (keyword_score, normalized_weights.keywords, True),
    }
    applicable_weight = sum(weight for _, weight, applicable in components.values() if applicable)
    final_score = sum(
        score * weight / applicable_weight
        for score, weight, applicable in components.values()
        if applicable
    )
    return ScoreBreakdown(
        skill_score=round(skill_score, 2),
        experience_score=round(experience_score, 2),
        education_score=round(education_score, 2),
        certification_score=round(cert_score, 2),
        keyword_score=round(keyword_score, 2),
        final_score=round(final_score, 2),
    )
