import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from backend.validator.contracts import ParsedJobDescriptionData, ParsedResumeData
from backend.taxonomy import get_taxonomy

SKILL_DICTIONARY = {
    "active directory",
    "apache airflow",
    "python",
    "fastapi",
    "django",
    "flask",
    "sqlalchemy",
    "postgresql",
    "sql",
    "mysql",
    "redis",
    "react",
    "typescript",
    "javascript",
    "aws",
    "azure",
    "docker",
    "kubernetes",
    "terraform",
    "linux",
    "ci/cd",
    "prometheus",
    "grafana",
    "machine learning",
    "nlp",
    "llm",
    "rag",
    "vector databases",
    "langchain",
    "mlflow",
    "pytorch",
    "tensorflow",
    "model deployment",
    "pandas",
    "numpy",
    "scikit-learn",
    "etl",
    "data modeling",
    "data cleaning",
    "data visualization",
    "snowflake",
    "spark",
    "dbt",
    "power bi",
    "tableau",
    "excel",
    "test automation",
    "api testing",
    "selenium",
    "playwright",
    "pytest",
    "postman",
    "identity access management",
    "privileged access management",
    "cyberark",
    "beyondtrust",
    "powershell",
    "saml",
    "oauth",
}

EDUCATION_TERMS = {
    "bachelor",
    "b.tech",
    "bsc",
    "master",
    "m.tech",
    "msc",
    "phd",
    "computer science",
    "engineering",
    "bachelor of engineering",
    "bachelor of technology",
    "b.e",
    "btech",
    "b.sc",
    "diploma",
    "information technology",
    "bca",
    "bba",
    "bcom",
    "b.com",
    "ba",
    "mca",
    "mba",
    "mcom",
    "m.com",
    "ma",
    "b.a",
    "m.sc",
    "ca intermediate",
    "data science",
    "psychology",
    "economics",
    "commerce",
    "business administration",
    "electronics",
}

CERTIFICATION_TERMS = {
    "aws certified",
    "azure certified",
    "gcp certified",
    "pmp",
    "scrum master",
    "cka",
    "ckad",
}


def normalize_tokens(values: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        token = re.sub(r"\s+", " ", value.strip().lower())
        if token and token not in seen:
            seen.add(token)
            normalized.append(token)
    return normalized


def extract_text_from_path(storage_path: str) -> str:
    path = Path(storage_path)
    if not path.exists():
        return ""
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return _extract_docx_text(path)
    data = path.read_bytes()
    return data.decode("utf-8", errors="ignore")


def parse_resume_text(raw_text: str) -> ParsedResumeData:
    text = raw_text.lower()
    sections = _extract_sections(raw_text)
    return ParsedResumeData(
        skills=[skill.casefold() for skill in get_taxonomy().extract_skills(raw_text)],
        total_experience_years=_extract_experience_years(text),
        education=_extract_education(text, sections.get("education", "")),
        certifications=_extract_certifications(text, sections.get("certifications", "")),
        projects=_extract_project_lines(sections.get("projects", "") or raw_text),
        sections=sections,
        raw_text=raw_text,
    )


SECTION_ALIASES = {
    "summary": {"summary", "professional summary", "profile", "career objective", "objective", "about me"},
    "experience": {"experience", "work experience", "professional experience", "employment history", "internships"},
    "skills": {"skills", "technical skills", "technical / professional skills", "professional skills", "core competencies", "technologies", "tools & technologies"},
    "education": {"education", "academic background", "academic qualifications", "qualifications"},
    "projects": {"projects", "academic projects", "personal projects", "projects & dashboards", "projects & case studies"},
    "certifications": {"certifications", "certificates", "licenses & certifications"},
    "achievements": {"achievements", "selected achievements", "awards", "honors", "accomplishments"},
    "languages": {"languages", "language proficiency"},
    "publications": {"publications", "research"},
    "volunteering": {"volunteering", "volunteer experience", "extracurricular activities"},
    "additional information": {"additional information", "personal details"},
}


def _extract_sections(raw_text: str) -> dict[str, str]:
    heading_lookup = {
        re.sub(r"[^a-z0-9& ]", "", alias.casefold()).strip(): canonical
        for canonical, aliases in SECTION_ALIASES.items()
        for alias in aliases
    }
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for line in raw_text.splitlines():
        cleaned = re.sub(r"[^a-z0-9& ]", "", line.casefold()).strip()
        candidate = cleaned.rstrip(":").strip()
        if candidate in heading_lookup and len(line.strip()) <= 60:
            current = heading_lookup[candidate]
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line.rstrip())
    return {
        name: "\n".join(lines).strip()
        for name, lines in sections.items()
        if "\n".join(lines).strip()
    }


def parse_job_description_text(
    *,
    description: str,
    skills_required: str,
    experience_min: int | None,
    experience_max: int | None,
    preferred_skills: str = "",
    education_requirements: str = "",
    certifications: str = "",
) -> ParsedJobDescriptionData:
    raw_text = (
        f"{description}\nRequired skills: {skills_required}"
        f"\nPreferred skills: {preferred_skills}"
        f"\nEducation: {education_requirements}"
        f"\nCertifications: {certifications}"
    )
    text = raw_text.lower()
    required = _canonical_skills(skills_required.split(","))
    return ParsedJobDescriptionData(
        required_skills=required,
        preferred_skills=_canonical_skills(preferred_skills.split(","))
        or _canonical_skills(_extract_preferred_skills(text)),
        experience_min=experience_min,
        experience_max=experience_max,
        education_requirements=_extract_education_requirements(education_requirements.lower())
        or _extract_education_requirements(text),
        certifications=_extract_terms(certifications.lower(), CERTIFICATION_TERMS)
        or _extract_terms(text, CERTIFICATION_TERMS),
        raw_text=raw_text,
    )


def _extract_terms(text: str, dictionary: set[str]) -> list[str]:
    return sorted(term for term in dictionary if re.search(rf"\b{re.escape(term)}\b", text))


def _canonical_skills(values: list[str]) -> list[str]:
    taxonomy = get_taxonomy()
    canonical: list[str] = []
    for value in normalize_tokens(values):
        skill = (taxonomy.canonicalize_skill(value) or value).casefold()
        if skill not in canonical:
            canonical.append(skill)
    return canonical


def _extract_experience_years(text: str) -> float:
    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\s+(?:of\s+)?experience",
        r"experience\s*[:\-]\s*(\d+(?:\.\d+)?)",
        r"total\s+experience\s*[:\-]\s*(\d+(?:\.\d+)?)",
    ]
    values: list[float] = []
    for pattern in patterns:
        values.extend(float(match) for match in re.findall(pattern, text))
    return max(values) if values else 0


def _extract_project_lines(raw_text: str) -> list[str]:
    projects: list[str] = []
    for line in raw_text.splitlines():
        if "project" in line.lower():
            projects.append(line.strip())
    return projects[:10]


def _extract_certifications(text: str, certification_section: str) -> list[str]:
    known = _extract_terms(text, CERTIFICATION_TERMS)
    section_values = []
    for line in certification_section.splitlines():
        value = re.sub(r"^[-*]\s*", "", line.strip()).strip()
        if not value:
            continue
        name = value.split("|", 1)[0].strip().casefold()
        if name:
            section_values.append(name)
    return normalize_tokens(known + section_values)


def _extract_education(text: str, education_section: str) -> list[str]:
    known = _extract_terms(text, EDUCATION_TERMS)
    section_values = []
    for line in education_section.splitlines():
        if "|" not in line:
            continue
        qualification = line.split("|", 1)[0].strip().casefold()
        if qualification and not re.fullmatch(r"\d{4}\s*-\s*(?:\d{4}|present)", qualification):
            section_values.append(qualification)
    return normalize_tokens(known + section_values)


def _extract_education_requirements(text: str) -> list[str]:
    values = _extract_terms(text, EDUCATION_TERMS)
    if re.search(r"\bIT\b", text, flags=re.IGNORECASE):
        values.append("information technology")
    return normalize_tokens(values)


def _extract_preferred_skills(text: str) -> list[str]:
    match = re.search(r"preferred skills?[ \t]*[:\-][ \t]*([^\n]+)", text)
    if not match:
        return []
    return normalize_tokens(re.split(r",|;", match.group(1)))


def _extract_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile):
        return path.read_bytes().decode("utf-8", errors="ignore")
    root = ElementTree.fromstring(xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    text_nodes = [node.text or "" for node in root.findall(".//w:t", namespace)]
    return " ".join(text_nodes)
