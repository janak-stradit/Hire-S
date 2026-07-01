from backend.validator.contracts import Thresholds


def classify_score(final_score: float, thresholds: Thresholds | None = None) -> str:
    active = thresholds or Thresholds()
    if final_score >= active.pass_score:
        return "PASS"
    if final_score >= active.review_score:
        return "REVIEW"
    return "FAIL"

