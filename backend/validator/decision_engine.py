from backend.validator.contracts import DecisionResult, Thresholds
from backend.validator.threshold_engine import classify_score

QUEUE_BY_DECISION = {
    "PASS": "R1 Queue",
    "REVIEW": "HR Review Queue",
    "FAIL": "Auto Reject Queue",
}


def make_decision(final_score: float, thresholds: Thresholds | None = None) -> DecisionResult:
    decision = classify_score(final_score, thresholds)
    return DecisionResult(decision=decision, queue_target=QUEUE_BY_DECISION[decision])

