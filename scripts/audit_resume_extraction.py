"""Audit structured resume extraction without writing to PostgreSQL."""

from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.excel_intake.workbooks import read_candidates
from backend.validator.resume_parser import parse_resume_text

REQUIRED_SECTIONS = ("summary", "experience", "skills", "education", "projects", "certifications")


def main() -> None:
    candidates, skipped = read_candidates(
        ROOT / "storage/candidate_pool/test_synthetic_candidates.xlsx", include_synthetic=True
    )
    missing: Counter[str] = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    missing_education_terms = 0
    missing_education_labels: Counter[str] = Counter()
    for candidate in candidates:
        parsed = parse_resume_text(candidate.raw_text)
        for section in REQUIRED_SECTIONS:
            if not parsed.sections.get(section, "").strip():
                missing[section] += 1
                if len(examples[section]) < 5:
                    examples[section].append(candidate.email)
        if not parsed.education:
            missing_education_terms += 1
            missing_education_labels[
                parsed.sections.get("education", "Unknown").splitlines()[0].split("|", 1)[0].strip()
            ] += 1
            if len(examples["education evidence"]) < 10:
                examples["education evidence"].append(
                    parsed.sections.get("education", candidate.email).splitlines()[0]
                )

    print(f"Candidates audited: {len(candidates)}; skipped: {skipped}")
    print(f"Missing structured sections: {dict(missing)}")
    print(f"Missing normalized education evidence: {missing_education_terms}")
    if missing_education_labels:
        print(f"Unrecognized education labels: {dict(missing_education_labels)}")
    if examples:
        print(f"Examples: {dict(examples)}")
    if missing or missing_education_terms:
        raise SystemExit(1)
    print("Resume section and education extraction: VERIFIED")


if __name__ == "__main__":
    main()
