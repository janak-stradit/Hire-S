"""Extract structured candidate fields from raw resume text.

Strategy (no LLM required):
  1. Regex patterns for deterministic fields (email, phone, URLs, experience years).
  2. Block-based section parser for work history (handles company-first AND role-first).
  3. Optional spaCy PERSON NER for name (falls back to heuristic with ALL-CAPS support).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# ── Compiled patterns ────────────────────────────────────────────────────────

_EMAIL    = re.compile(r"[\w.+\-]+@[\w\-]+\.[\w.\-]+", re.I)
_PHONE    = re.compile(
    r"(?:\+?91[\s\-]?)?(?:\(?\d{3,5}\)?[\s\-]?\d{5,6}|\d{10}|\d{5}[\s\-]\d{5})",
    re.I,
)
_LINKEDIN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-%.]+", re.I)
_GITHUB   = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w\-%.]+", re.I)
_PORTFOLIO = re.compile(
    r"(?:https?://)?(?:www\.)?(?:portfolio\.[\w.]+|behance\.net|dribbble\.com)/[\w\-%.]+",
    re.I,
)

# ── Date patterns ──────────────────────────────────────────────────────────
_MONTH_PAT = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?"

# Full date range: "Jan 2020 – Present", "2018 - 2021", "06/2020 - Present"
_DATE_RANGE = re.compile(
    r"(?:" + _MONTH_PAT + r"\s+)?\d{4}"
    r"\s*[-–/to]+\s*"
    r"(?:(?:" + _MONTH_PAT + r"\s+)?\d{4}|present|till\s+date|current|now|ongoing)",
    re.I,
)

# Standalone year or month-year
_YEAR_ONLY = re.compile(r"^\d{4}$")

# ── Experience years ───────────────────────────────────────────────────────
# Matches "5 years", "5.5 years", "5 yrs 6 months" etc.
_EXP_YEARS  = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", re.I)
_EXP_MONTHS = re.compile(r"(\d+)\s*\+?\s*months?", re.I)

# ── Salary ─────────────────────────────────────────────────────────────────
_SALARY = re.compile(
    r"(?:₹|Rs\.?|INR\s*)?(\d+(?:\.\d+)?)\s*(?:L(?:PA|AKH)?|lpa|lakhs?|CTC|ctc)",
    re.I,
)
_SAL_CONTEXTS = re.compile(
    r"expected\s+(?:ctc|salary|compensation|package)|"
    r"ctc\s+expected|desired\s+(?:ctc|salary)|"
    r"salary\s+expected|expected\s+salary",
    re.I,
)

# ── Notice period ──────────────────────────────────────────────────────────
_NOTICE_LABEL = re.compile(r"notice\s+period", re.I)
_NOTICE_VAL   = re.compile(
    r"(immediate|immediately|serving\s+notice|\d+\s*(?:days?|weeks?|months?))",
    re.I,
)

# ── Education ──────────────────────────────────────────────────────────────
_DEGREES = {
    "b.tech": "B.Tech", "b.e.": "B.E.", "b.e ": "B.E.", "b.sc": "B.Sc.",
    "bsc ": "B.Sc.", "bsc,": "B.Sc.",
    "m.tech": "M.Tech", "m.e.": "M.E.", "m.e ": "M.E.", "mca": "MCA",
    "bca": "BCA", "mba": "MBA", "b.com": "B.Com", "m.com": "M.Com",
    "b.a.": "B.A.", "m.a.": "M.A.", "ph.d": "Ph.D.", "phd": "Ph.D.",
    "diploma": "Diploma", "10+2": "10+2 / HSC", "12th": "12th / HSC",
    "bachelor": "Bachelor's", "master": "Master's",
}

# ── Location ───────────────────────────────────────────────────────────────
_CITIES = {
    "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad", "chennai",
    "pune", "kolkata", "ahmedabad", "jaipur", "surat", "lucknow", "noida",
    "gurgaon", "gurugram", "chandigarh", "indore", "bhopal", "nagpur",
    "coimbatore", "kochi", "cochin", "vizag", "visakhapatnam", "remote",
    "thane", "navi mumbai", "vadodara", "patna", "ranchi", "mysore",
    "mysuru", "bhubaneswar", "thiruvananthapuram", "trivandrum",
}
_STATES = {
    "maharashtra", "karnataka", "telangana", "andhra pradesh", "tamil nadu",
    "kerala", "gujarat", "rajasthan", "uttar pradesh", "madhya pradesh",
    "punjab", "haryana", "west bengal", "odisha", "jharkhand", "bihar",
}

# ── Section headers ────────────────────────────────────────────────────────
_SKILLS_HEADERS = re.compile(
    r"^(?:(?:technical|key|core|primary|relevant)\s+)?skills?\s*(?:summary|set|profile|highlights?)?\s*:?\s*$",
    re.I,
)
_SKILLS_INLINE = re.compile(
    r"^(?:(?:technical|key|core|primary|relevant)\s+)?skills?\s*(?:summary|set|profile|highlights?)?\s*[:–\-]\s*(.+)",
    re.I,
)

_EXP_HEADERS = re.compile(
    r"^(?:work\s+|professional\s+)?(?:experience|employment|work\s+history|"
    r"career(?:\s+summary)?|professional\s+experience|professional\s+background)\s*:?\s*$",
    re.I,
)
_EDU_HEADERS = re.compile(
    r"^(?:education(?:al)?\s*(?:qualification)?|academic(?:\s+background)?|"
    r"qualifications?)\s*:?\s*$",
    re.I,
)

# Sections that end the experience block
_STOP_SECTION = re.compile(
    r"^(?:education|skills?|technical\s+skills?|key\s+skills?|"
    r"projects?|certifications?|academic|activities|achievements|"
    r"publications?|references?|interests?|hobbies|languages?|"
    r"extra.?curricular|awards?|honours?|personal\s+details?)\s*:?\s*$",
    re.I,
)

# ── Role / Company keywords ────────────────────────────────────────────────
_ROLE_KW = re.compile(
    r"\b(?:engineer|developer|analyst|manager|lead|architect|designer|"
    r"consultant|specialist|executive|officer|associate|intern|trainee|"
    r"scientist|administrator|coordinator|director|head|vp|cto|ceo|coo|"
    r"programmer|tester|qa|devops|sre|data|backend|frontend|fullstack|"
    r"full.?stack|mobile|android|ios|cloud|security|network|system|"
    r"software|technical|principal|senior|junior|sr\.|jr\.)\b",
    re.I,
)
_CO_KW = re.compile(
    r"\b(?:pvt\.?|ltd\.?|limited|inc\.?|llc|corp\.?|co\.?|"
    r"technologies|technology|tech|solutions|services|systems|"
    r"group|consulting|global|international|enterprises?|agency|"
    r"infosys|wipro|tcs|accenture|cognizant|capgemini|ibm|"
    r"microsoft|google|amazon|meta|apple|flipkart|zomato|swiggy|"
    r"ola|paytm|razorpay|freshworks|zoho|mphasis|hexaware|"
    r"l&t|larsen|hcl|tech\s*mahindra|mindtree|persistent)\b",
    re.I,
)

# Inline job: "Role - Company", "Role @ Company", "Role at Company", "Role | Company"
_JOB_INLINE_SEP = re.compile(
    r"^(.+?)\s+(?:at|@|-|–|\|)\s+(.+?)(?:\s*[,(]|\s*$)",
    re.I,
)
# "Role, Company Ltd" — comma separation with corporate suffix on right side
_JOB_INLINE_COMMA = re.compile(
    r"^(.+?),\s+(.+?(?:pvt|ltd|limited|solutions|technologies|tech|services|systems|inc|llc|group|consulting)\.?)\s*$",
    re.I,
)

# Lines to skip inside experience blocks (bullets, descriptions)
_BULLET = re.compile(r"^[•\-\*\–·▪▸►◦‣]\s*")
_RESP_KW = re.compile(
    r"^(?:responsible|designed|developed|implemented|led|managed|built|created|"
    r"delivered|worked|collaborated|maintained|optimized|deployed|drove|achieved|"
    r"increased|decreased|reduced|improved|migrated|handled|participated)",
    re.I,
)


# ── Output dataclasses ────────────────────────────────────────────────────

@dataclass
class WorkEntry:
    role: str
    company: str
    duration: str

    def to_dict(self) -> dict:
        return {"role": self.role, "company": self.company, "duration": self.duration}


@dataclass
class ParsedResume:
    first_name: str | None        = None
    last_name: str | None         = None
    email: str | None             = None
    phone: str | None             = None
    city: str | None              = None
    state: str | None             = None
    country: str                  = "India"
    current_role: str | None      = None
    current_company: str | None   = None
    total_experience: float | None = None
    expected_salary: int | None   = None
    notice_period: str | None     = None
    highest_education: str | None = None
    linkedin_url: str | None      = None
    github_url: str | None        = None
    portfolio_url: str | None     = None
    skills: list[str]             = field(default_factory=list)
    work_history: list[WorkEntry] = field(default_factory=list)
    raw_text: str                 = ""


# ── Core parser ───────────────────────────────────────────────────────────

def parse_resume(text: str) -> ParsedResume:
    result = ParsedResume(raw_text=text)
    lines  = [ln.strip() for ln in text.splitlines()]
    # Non-empty lines joined for full-text regex
    clean  = " ".join(l for l in lines if l)

    # ── Email ──────────────────────────────────────────────────────────────
    m = _EMAIL.search(clean)
    result.email = m.group(0).lower() if m else None

    # ── Phone ──────────────────────────────────────────────────────────────
    # Remove email from clean text before phone search to avoid matching domain digits
    phone_text = _EMAIL.sub(" ", clean)
    m = _PHONE.search(phone_text)
    if m:
        phone = re.sub(r"[\s\-()]", "", m.group(0))
        if len(phone) >= 10:
            result.phone = phone

    # ── URLs ───────────────────────────────────────────────────────────────
    m = _LINKEDIN.search(clean)
    result.linkedin_url = m.group(0) if m else None
    m = _GITHUB.search(clean)
    result.github_url = m.group(0) if m else None
    m = _PORTFOLIO.search(clean)
    result.portfolio_url = m.group(0) if m else None

    # ── Experience years ───────────────────────────────────────────────────
    # Look for explicit "X years Y months" declarations first
    exp_ctx = re.search(
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s*(?:(?:and\s*)?(\d+)\s*months?)?",
        clean, re.I,
    )
    if exp_ctx:
        yrs  = float(exp_ctx.group(1))
        mos  = int(exp_ctx.group(2)) if exp_ctx.group(2) else 0
        result.total_experience = round(yrs + mos / 12, 1)

    # ── Notice period ──────────────────────────────────────────────────────
    result.notice_period = _extract_notice_period(lines)

    # ── Salary ────────────────────────────────────────────────────────────
    result.expected_salary = _extract_salary(clean)

    # ── Education ─────────────────────────────────────────────────────────
    result.highest_education = _extract_education(clean)

    # ── Location ──────────────────────────────────────────────────────────
    result.city, result.state = _extract_location(lines)

    # ── Name ──────────────────────────────────────────────────────────────
    name = _extract_name(lines, result.email)
    if name:
        parts = name.split()
        result.first_name = parts[0].title()
        result.last_name  = " ".join(parts[1:]).title() if len(parts) > 1 else None

    # ── Skills ────────────────────────────────────────────────────────────
    result.skills = _extract_skills(lines)

    # ── Work history ──────────────────────────────────────────────────────
    result.work_history = _extract_work_history(lines)

    # Current role/company from most-recent work entry
    if result.work_history:
        first = result.work_history[0]
        if first.role:
            result.current_role = first.role
        if first.company:
            result.current_company = first.company

    return result


# ── Field extractors ──────────────────────────────────────────────────────

def _extract_name(lines: list[str], email: str | None) -> str | None:
    """
    Order: strict heuristic first (most reliable), then spaCy with position
    constraint, then relaxed heuristic.
    """
    skip = re.compile(
        r"[@|/]|\d{4,}|http|www|resume|cv|curriculum|vitae|profile|"
        r"objective|summary|engineer|developer|analyst|manager|consultant|"
        r"experience|skills|education",
        re.I,
    )

    # Pass 1: strict heuristic – pure-alpha title-case or ALL-CAPS, 2-4 words
    for line in lines[:8]:
        if not line or skip.search(line):
            continue
        words = line.split()
        if 2 <= len(words) <= 4:
            # Title Case: "Priya Sharma"
            if all(re.match(r"^[A-Z][a-z]{1,}$", w) for w in words):
                return line
            # ALL CAPS: "RAJESH KUMAR"
            if all(re.match(r"^[A-Z]{2,}$", w) for w in words):
                return line.title()

    # Pass 2: spaCy — only accept entities that start within the first 80 chars
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        head = "\n".join(lines[:8])
        doc  = nlp(head)
        for ent in doc.ents:
            if ent.label_ == "PERSON" and ent.start_char < 80:
                name = _clean_name_token(ent.text)
                if name and 2 <= len(name.split()) <= 4:
                    return name
    except Exception:
        pass

    # Pass 3: relaxed — handles initials like "S.K. Sharma", "Md. Tariq"
    for line in lines[:8]:
        if not line or skip.search(line):
            continue
        words = line.split()
        if 2 <= len(words) <= 4:
            if all(re.match(r"^[A-Z][a-z]*\.?$|^[A-Z]{1,3}\.?$", w) for w in words):
                return " ".join(w.rstrip(".").title() for w in words)
    return None


def _clean_name_token(raw: str) -> str:
    raw = _EMAIL.sub("", raw)
    raw = re.sub(r"[^A-Za-z\s\-']", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    words = raw.split()
    # Reject if any word looks like a job title
    if any(_ROLE_KW.search(w) for w in words):
        return ""
    return " ".join(words[:4]) if words else ""


def _extract_location(lines: list[str]) -> tuple[str | None, str | None]:
    city: str | None  = None
    state: str | None = None

    for line in lines[:30]:
        lower = line.lower()

        if not city:
            for c in _CITIES:
                if c in lower:
                    city = c.title()
                    break

        if not state:
            for s in _STATES:
                if s in lower:
                    state = s.title()
                    break

        if city and state:
            break

    return city, state


def _extract_notice_period(lines: list[str]) -> str | None:
    """Only extract when 'notice period' label is present on the line."""
    for line in lines:
        if _NOTICE_LABEL.search(line):
            m = _NOTICE_VAL.search(line)
            if m:
                return m.group(1).strip().title()
    return None


def _extract_salary(clean: str) -> int | None:
    """Find expected salary near known salary-context phrases."""
    m = _SAL_CONTEXTS.search(clean)
    if m:
        # Look within 80 chars after the label
        snippet = clean[m.start():m.start() + 120]
        sm = _SALARY.search(snippet)
        if sm:
            return int(float(sm.group(1)) * 100_000)
    return None


def _extract_education(clean: str) -> str | None:
    lower = clean.lower()
    for key, label in sorted(_DEGREES.items(), key=lambda x: -len(x[0])):
        if key in lower:
            return label
    return None


def _extract_skills(lines: list[str]) -> list[str]:
    """
    Two-pass extraction:
    1. Inline skill lines:  "Key Skills: Python | Django | REST APIs"
    2. Block after header:  "TECHNICAL SKILLS\nPython\nDjango\n..."
    """
    skills: list[str] = []
    seen:  set[str]   = set()
    in_skills          = False

    def _add(tokens: str) -> None:
        for tok in re.split(r"[,|•●\*•·;/]", tokens):
            tok = tok.strip().strip("()")
            if 2 <= len(tok) <= 60 and tok and not tok[0].isdigit():
                key = tok.lower()
                if key not in seen:
                    seen.add(key)
                    skills.append(tok)

    for line in lines:
        # Inline: "Key Skills: ..." — add skills and mark section as started
        m = _SKILLS_INLINE.match(line)
        if m:
            in_skills = True
            _add(m.group(1))
            continue

        # Block header: "TECHNICAL SKILLS"
        if _SKILLS_HEADERS.search(line):
            in_skills = True
            continue

        # Stop when we hit any recognisable section header
        if in_skills and (_EXP_HEADERS.search(line) or _EDU_HEADERS.search(line)
                          or _STOP_SECTION.search(line)):
            break

        if in_skills and line:
            # Stop if line looks like a responsibility sentence (not a skill)
            if _RESP_KW.match(line) or _BULLET.match(line):
                break
            _add(line)

    return skills[:40]


def _parse_job_line(line: str) -> tuple[str | None, str | None]:
    """Try to extract (role, company) from a single inline line."""
    # "Role - Company", "Role @ Company", "Role at Company"
    m = _JOB_INLINE_SEP.match(line)
    if m:
        p1, p2 = m.group(1).strip(), m.group(2).strip()
        # Disambiguate which is role vs company
        if _ROLE_KW.search(p1) and not _ROLE_KW.search(p2):
            return _clean_field(p1), _clean_field(p2)
        if _CO_KW.search(p2) and not _CO_KW.search(p1):
            return _clean_field(p1), _clean_field(p2)
        if _CO_KW.search(p1):
            return _clean_field(p2), _clean_field(p1)
        return _clean_field(p1), _clean_field(p2)

    # "Role, Company Ltd"
    m = _JOB_INLINE_COMMA.match(line)
    if m:
        return _clean_field(m.group(1).strip()), _clean_field(m.group(2).strip())

    return None, None


def _extract_work_history(lines: list[str]) -> list[WorkEntry]:
    """
    Block-based approach:
    1. Find the experience section.
    2. Split into blocks (groups separated by blank lines or new-entry signals).
    3. Parse each block: identify role, company, duration regardless of order.
    """
    # ── Find experience section ────────────────────────────────────────────
    exp_start: int | None = None
    exp_end   = len(lines)

    for i, line in enumerate(lines):
        if _EXP_HEADERS.search(line):
            exp_start = i + 1
        elif exp_start is not None and _STOP_SECTION.search(line):
            exp_end = i
            break

    if exp_start is None:
        return []

    exp_lines = lines[exp_start:exp_end]

    # ── Split into candidate blocks ───────────────────────────────────────
    # A new block starts after a blank line OR when we detect a clear new-entry signal.
    blocks: list[list[str]] = []
    cur: list[str] = []

    for line in exp_lines:
        if not line:
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(line)
    if cur:
        blocks.append(cur)

    # ── Parse each block ──────────────────────────────────────────────────
    entries: list[WorkEntry] = []

    for block in blocks:
        role:     str | None = None
        company:  str | None = None
        duration: str | None = None

        for line in block:
            # Skip bullet points and responsibility lines
            if _BULLET.match(line) or _RESP_KW.match(line):
                continue

            # ── Date range ──────────────────────────────────────────────
            dr = _DATE_RANGE.search(line)
            if dr and not duration:
                duration = dr.group(0).strip()
            # Remove date range from line for further matching
            clean_line = _DATE_RANGE.sub("", line).strip(" |-()")
            if not clean_line:
                continue

            # ── Inline formats ──────────────────────────────────────────
            if not role or not company:
                r_try, c_try = _parse_job_line(clean_line)
                if r_try and c_try:
                    role    = role    or r_try
                    company = company or c_try
                    continue

            # ── Single-field line ───────────────────────────────────────
            # Is it a role?
            if _ROLE_KW.search(clean_line) and len(clean_line.split()) <= 10:
                if not role:
                    role = _clean_field(clean_line)
                continue

            # Is it a company?
            if _CO_KW.search(clean_line):
                if not company:
                    company = _clean_field(clean_line)
                continue

            # Short title-case / ALL-CAPS line — might be company or role
            words = clean_line.split()
            if 1 <= len(words) <= 6:
                if not company and (
                    clean_line[0].isupper() or clean_line.isupper()
                ) and not _ROLE_KW.search(clean_line):
                    company = _clean_field(clean_line)
                elif not role and _ROLE_KW.search(clean_line):
                    role = _clean_field(clean_line)

        if role or company:
            entries.append(WorkEntry(
                role    = role    or "",
                company = company or "",
                duration= duration or "",
            ))

    return entries[:10]


def _clean_field(s: str | None) -> str | None:
    if not s:
        return None
    # Remove trailing date info
    s = re.sub(r"\s*[\(\[]\s*\d{4}.*$", "", s)
    s = re.sub(r"\s*[-–]\s*(?:\d{4}|present|current|till|now).*$", "", s, flags=re.I)
    s = re.sub(r"\s*\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b.*$", "", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(".-,| ").strip()
    return s[:180] or None
