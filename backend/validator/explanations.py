from backend.validator.contracts import ScoreBreakdown


def build_explanation(
    scores: ScoreBreakdown,
    decision: str,
    matched_skills: list[str] | None = None,
    missing_skills: list[str] | None = None,
) -> str:
    strengths: list[str] = []
    risks: list[str] = []
    if scores.skill_score >= 75:
        strengths.append("strong skill alignment")
    elif scores.skill_score < 60:
        risks.append("skill alignment is below target")
    if scores.experience_score >= 75:
        strengths.append("sufficient experience")
    elif scores.experience_score < 60:
        risks.append("experience is below the required range")
    if scores.keyword_score >= 75:
        strengths.append("high resume-to-job keyword relevance")
    elif scores.keyword_score < 50:
        risks.append("low keyword relevance")

    if decision == "PASS":
        basis = " and ".join(strengths[:2]) or "overall match exceeds the pass threshold"
    elif decision == "REVIEW":
        basis = "; ".join(risks[:2] or strengths[:2]) or "candidate is near the review threshold"
    else:
        basis = "; ".join(risks[:2]) or "overall match is below the review threshold"
    skill_detail = (
        f" Matched required skills: {', '.join(matched_skills or []) or 'none'}."
        f" Missing required skills: {', '.join(missing_skills or []) or 'none'}."
    )
    return (
        f"Candidate Score = {scores.final_score}. Skills Match = {scores.skill_score}. "
        f"Experience Match = {scores.experience_score}. Education Match = {scores.education_score}. "
        f"Certifications Match = {scores.certification_score}. Keywords Match = {scores.keyword_score}. "
        f"Decision = {decision}. Reason: {basis}.{skill_detail}"
    )
