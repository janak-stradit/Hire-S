DEGREE_LEVELS = {
    "bachelor": {"bachelor", "b.tech", "btech", "b.e", "be", "bsc", "b.sc", "bca", "bba", "bcom", "b.com", "b.a", "ba", "undergraduate"},
    "master": {"master", "m.tech", "mtech", "m.e", "me", "msc", "m.sc", "mca", "mba", "mcom", "m.com", "m.a", "ma", "postgraduate"},
    "phd": {"phd", "doctorate"},
    "diploma": {"diploma"},
}

FIELD_GROUPS = {
    "computing": {"computer science", "information technology", "data science"},
    "electronics": {"electronics", "electronics engineering"},
    "business": {"business administration", "commerce", "economics"},
    "psychology": {"psychology"},
    "engineering": {"engineering"},
}


def education_match_score(candidate_education: list[str], required_education: list[str]) -> float:
    if not required_education:
        return 100.0
    if not candidate_education:
        return 0.0
    candidate = {_canonical(term) for term in candidate_education}
    required = {_canonical(term) for term in required_education}
    dimension_scores: list[float] = []

    required_degrees = required.intersection(DEGREE_LEVELS)
    if required_degrees:
        candidate_degrees = candidate.intersection(DEGREE_LEVELS)
        dimension_scores.append(100.0 if candidate_degrees.intersection(required_degrees) else 0.0)

    required_fields = {_field_group(term) for term in required if _field_group(term)}
    if required_fields:
        candidate_fields = {_field_group(term) for term in candidate if _field_group(term)}
        dimension_scores.append(100.0 if candidate_fields.intersection(required_fields) else 0.0)

    remaining = required.difference(required_degrees).difference(
        term for term in required if _field_group(term)
    )
    if remaining:
        dimension_scores.append((len(candidate.intersection(remaining)) / len(remaining)) * 100)
    return round(sum(dimension_scores) / len(dimension_scores), 2) if dimension_scores else 100.0


def _canonical(term: str) -> str:
    normalized = term.strip().casefold()
    for canonical, aliases in DEGREE_LEVELS.items():
        if any(normalized == alias or normalized.startswith(f"{alias} ") for alias in aliases):
            return canonical
    return normalized


def _field_group(term: str) -> str | None:
    normalized = term.strip().casefold()
    for group, aliases in FIELD_GROUPS.items():
        if any(normalized == alias or alias in normalized for alias in aliases):
            return group
    return None
