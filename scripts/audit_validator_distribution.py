"""Score an intake workbook without writing candidates or decisions to PostgreSQL."""

from collections import Counter
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.excel_intake.workbooks import read_candidates, read_requirement
from backend.validator.contracts import Thresholds
from backend.validator.decision_engine import make_decision
from backend.validator.resume_parser import parse_job_description_text, parse_resume_text
from backend.validator.scoring import calculate_scores


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requirement", default="REQ-IT-SUPPORT-ENGINEER-001")
    parser.add_argument("--pool", choices=("real", "synthetic"), default="synthetic")
    args = parser.parse_args()
    root = ROOT
    workbook = (
        "test_synthetic_candidates.xlsx" if args.pool == "synthetic" else "hirex_candidates.xlsx"
    )
    candidates, skipped = read_candidates(
        root / f"storage/candidate_pool/{workbook}", include_synthetic=args.pool == "synthetic"
    )
    requirement = read_requirement(
        root / "storage/job_requirements/jd_input.xlsx", args.requirement
    )
    job = parse_job_description_text(
        description=requirement.jd_text,
        skills_required=",".join(requirement.required_skills),
        preferred_skills=",".join(requirement.preferred_skills),
        experience_min=requirement.experience_min,
        experience_max=requirement.experience_max,
        education_requirements=requirement.education,
        certifications=",".join(requirement.mandatory_certifications),
    )
    thresholds = Thresholds(
        pass_score=requirement.screening_pass_score,
        review_score=requirement.screening_review_score,
    )
    decisions: Counter[str] = Counter()
    role_decisions: Counter[tuple[str, str]] = Counter()
    scores: list[float] = []
    role_population: Counter[str] = Counter()
    for candidate in candidates:
        resume = parse_resume_text(candidate.raw_text)
        resume.total_experience_years = max(
            resume.total_experience_years, candidate.total_experience or 0
        )
        if candidate.highest_education:
            profile_education = parse_resume_text(candidate.highest_education).education
            resume.education = list(dict.fromkeys(resume.education + profile_education))
        score = calculate_scores(resume, job).final_score
        decision = make_decision(score, thresholds).decision
        decisions[decision] += 1
        role_decisions[(candidate.current_role or "Unspecified", decision)] += 1
        role_population[candidate.current_role or "Unspecified"] += 1
        scores.append(score)

    print(f"Requirement: {requirement.role} ({requirement.requirement_id})")
    print(f"Candidates: {len(candidates)}; skipped: {skipped}")
    print(f"Decisions: {dict(decisions)}")
    print(f"Scores: min={min(scores):.2f}, avg={sum(scores) / len(scores):.2f}, max={max(scores):.2f}")
    print("Top non-fail roles:")
    non_fail = Counter()
    for (role, decision), count in role_decisions.items():
        if decision != "FAIL":
            non_fail[role] += count
    for role, count in non_fail.most_common(12):
        print(f"  {role}: {count}")
    related_roles = Counter(
        {role: count for role, count in role_population.items() if "frontend" in role.casefold()}
    )
    print(f"Frontend-role population: {sum(related_roles.values())}")
    for role, count in related_roles.most_common():
        print(f"  {role}: {count}")


if __name__ == "__main__":
    main()
