def experience_match_score(candidate_years: float, required_min: int | None, required_max: int | None) -> float:
    if required_min is None and required_max is None:
        return 100.0
    minimum = required_min or 0
    maximum = required_max
    if candidate_years >= minimum and (maximum is None or candidate_years <= maximum + 2):
        return 100.0
    if candidate_years < minimum:
        if minimum == 0:
            return 100.0
        return round(max(0.0, (candidate_years / minimum) * 100), 2)
    if maximum is not None and candidate_years > maximum + 2:
        excess = candidate_years - maximum
        return round(max(70.0, 100.0 - excess * 5), 2)
    return 75.0

