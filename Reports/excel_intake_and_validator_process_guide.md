# HireX Excel Intake and Validator Process Guide

Date: 2026-06-21

## Threshold Routing

Each active job requirement supplies two values:

- `screening_pass_score`: candidates at or above this score receive `PASS` and enter `R1 Queue`.
- `screening_review_score`: candidates at or above this score but below pass receive `REVIEW` and enter `HR Review Queue`.
- Candidates below the review score receive `FAIL` and enter `Auto Reject Queue`.

For the active IT Support Engineer requirement:

- Score `>= 72`: R1 Screening Agent.
- Score `>= 58` and `< 72`: HR review.
- Score `< 58`: rejected.

## Score Calculation

The default final score is a normalized weighted score:

- Required skill match: 40%.
- Experience match: 25%.
- Education match: 10%.
- Mandatory certification match: 10%.
- Resume/JD keyword relevance, including preferred skills: 15%.

Preferred skills influence keyword relevance but are not treated as mandatory skill gates.
When no mandatory certification is supplied, certification matching receives a neutral score of 100.

## Implemented Process

1. HR maintains requirements in `storage/job_requirements/jd_input.xlsx`.
2. Exactly one requirement must be marked `active`; other roles remain `draft` or `closed`.
3. The intake service validates columns, ranges, thresholds, and active-row uniqueness.
4. The service reads only candidates with `agent_processing_allowed=true` from the real candidate pool.
5. Synthetic candidates stay in a separate workbook and are disabled by default.
6. The active job is inserted or updated in PostgreSQL using its stable `requirement_id`.
7. Candidates are deduplicated by normalized email and inserted or updated in `users` and `candidate_profiles`.
8. Resume metadata is stored in `resumes`, and source provenance remains attached to the profile.
9. An `IMPORTED` application connects every eligible candidate to the active job.
10. Resume source text and the JD are parsed into normalized skills, experience, education, certifications, and keywords.
11. The validator calculates component scores and the weighted final score.
12. The threshold engine assigns PASS, REVIEW, or FAIL and stores the result in `validator_results`.
13. PASS candidates are available from `GET /api/validator/queues/r1` for the screening/calling agent.
14. REVIEW candidates remain available to HR for a manual decision.
15. FAIL candidates remain retained for audit and are not sent to R1.
16. PASS and REVIEW candidates are exported to `storage/shortlisted`; FAIL candidates go to `storage/rejected`.
17. Counts, paths, status, and errors are recorded in `excel_intake_batches`.

## Job Catalog

The workbook contains ten requirements:

- Data Engineer: draft, thresholds 75/60.
- AI Engineer: draft, thresholds 78/62.
- Machine Learning Engineer: draft, thresholds 78/62.
- Data Analyst: draft, thresholds 72/58.
- Backend Engineer: draft, thresholds 75/60.
- Frontend Engineer: draft, thresholds 74/59.
- DevOps Engineer: draft, thresholds 76/60.
- QA Automation Engineer: draft, thresholds 73/58.
- IAM / PAM Engineer: draft, thresholds 75/60.
- IT Support Engineer: active, thresholds 72/58.

To screen another role, change IT Support Engineer to `draft` or `closed` and change exactly one other row to `active`.

## Candidate Portal Compatibility

Excel does not replace or alter the core architecture. It currently creates the same database records
that the candidate portal will create later. When the portal is enabled, its intake path can be used
instead of Excel while the validator, thresholds, PostgreSQL tables, R1 queue, and downstream agents
continue unchanged.
