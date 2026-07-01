from difflib import SequenceMatcher
import re

from backend.validator.contracts import SkillMatchResult

try:
    from rapidfuzz import fuzz
except ModuleNotFoundError:
    fuzz = None


SKILL_EQUIVALENTS: dict[str, set[str]] = {
    "technical troubleshooting": {"troubleshooting", "problem diagnosis", "root cause analysis"},
    "ticketing systems": {"servicenow", "jira service management", "jira service desk", "ticketing", "incident management", "help desk"},
    "hardware support": {"hardware", "desktop support", "endpoint support", "asset management"},
    "network basics": {"networking", "tcp/ip", "dns", "dhcp", "lan/wan", "network support"},
    "it support": {"technical support", "desktop support", "help desk", "service desk"},
    "microsoft 365": {"office 365", "o365"},
}


def match_skills(
    resume_skills: list[str], required_skills: list[str], resume_text: str = ""
) -> SkillMatchResult:
    if not required_skills:
        return SkillMatchResult(score=100.0)
    normalized_resume = {_normalize(skill) for skill in resume_skills if _normalize(skill)}
    normalized_text = _normalize(resume_text)
    matched: list[str] = []
    missing: list[str] = []
    evidence: dict[str, list[str]] = {}
    for required in required_skills:
        normalized_required = _normalize(required)
        candidates = {normalized_required, *SKILL_EQUIVALENTS.get(normalized_required, set())}
        found = sorted({term for term in candidates if _has_evidence(term, normalized_resume, normalized_text)})
        if not found:
            fuzzy = sorted(
                skill for skill in normalized_resume if _safe_fuzzy_match(normalized_required, skill)
            )
            found = fuzzy[:1]
        if found:
            matched.append(normalized_required)
            evidence[normalized_required] = found
        else:
            missing.append(normalized_required)
    score = round((len(matched) / len(set(map(_normalize, required_skills)))) * 100, 2)
    return SkillMatchResult(score=score, matched_skills=matched, missing_skills=missing, evidence=evidence)


def skill_match_score(resume_skills: list[str], required_skills: list[str]) -> float:
    return match_skills(resume_skills, required_skills).score


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


def _has_evidence(term: str, resume_skills: set[str], resume_text: str) -> bool:
    return term in resume_skills or bool(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", resume_text))


def _safe_fuzzy_match(required: str, candidate: str) -> bool:
    if min(len(required), len(candidate)) < 5:
        return False
    return _similarity(required, candidate) >= 92


def _similarity(left: str, right: str) -> float:
    if fuzz is not None:
        return float(fuzz.token_set_ratio(left, right))
    return SequenceMatcher(None, left.lower(), right.lower()).ratio() * 100
