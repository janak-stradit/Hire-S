# HireX Validator Integrity and HR Workflow Execution Report

Date: 2026-06-21

## Incident

The first synthetic validator batch completed in PostgreSQL but produced 1,000 FAIL decisions. The browser later reported the request as failed because the synchronous run exceeded the practical request window. Investigation found that required skills were matched too literally, neutral certification requirements inflated fixed weighting, resume sections were not exposed structurally, and each candidate evaluation committed separately.

## Corrections

- Added controlled skill equivalence evidence while retaining strict fuzzy-match safeguards.
- Persisted matched skills, missing skills, evidence, and scoring version for every result.
- Excluded non-applicable education or certification dimensions from weighted scoring.
- Updated application status to SHORTLISTED, UNDER_REVIEW, or REJECTED with each validator decision.
- Added complete named resume-section extraction while retaining the original resume text.
- Optimized taxonomy extraction with one cached longest-first matcher.
- Changed Excel intake to one batch commit instead of one commit per candidate.
- Added immutable HR decisions and workflow views for Awaiting HR, Moved forward, Held, and Rejected.
- Removed candidate-only navigation from HR, recruiter, and admin workspaces.
- Expanded JD entry to include role, department, location, employment type, experience, required and preferred skills, mandatory certifications, salary, education, thresholds, status, and full JD text.
- Added authenticated `/api/auth/me` role resolution and explicit 401/403 UI handling.

## Production Rerun

- Batch: `ae46ee3e-a7f8-4420-a9e4-bb645e34fc1c`
- Requirement: `REQ-IT-SUPPORT-ENGINEER-001`
- Candidate pool: synthetic simulation
- Imported: 1,000
- PASS: 123
- REVIEW: 11
- FAIL: 866
- Runtime: 47.8 seconds
- Previous all-FAIL batch status: SUPERSEDED

Synthetic candidates remain blocked from agent handoff by `agent_processing_allowed = false`.

### Scoring 2.2 extraction correction

- Batch: `55ab660f-58f3-48c2-a15e-c594a1e09ac3`
- Added direct validator-result batch provenance.
- Audited 1,000 resumes with zero missing summary, experience, skills, education, projects, or certification sections.
- Added common Indian degree normalization including BCA, BBA, B.Com, B.A., MCA, MBA, M.Com, M.A., M.Sc., and CA Intermediate evidence.
- Corrected extended headings such as Technical / Professional Skills, Projects & Case Studies, Selected Achievements, and Additional Information.
- Final distribution: 131 PASS, 3 REVIEW, 866 FAIL.
- Candidate lists now use server-side pagination with 25 records per page.
- Rejected candidates include a focused rejection-reason modal with score, review threshold, missing required skills, and the persisted validator explanation.
- Rejected-only verification covered all 866 FAIL results: complete required resume sections, non-empty raw text, complete required-skill mapping, scores below the review threshold, and REJECTED application status.
- Candidate evidence now uses one structured score layout across PASS, REVIEW, HOLD, and FAIL: threshold outcome, applicable score dimensions, matched and missing requirements, strong evidence, review concerns, and a collapsed immutable audit record.

## Verification

- PostgreSQL batch invariant verification: passed for all 1,000 records.
- Backend tests: 31 passed.
- Next.js production build: passed.
- Alembic schema drift check: passed.
- No-write distribution audit: 123 PASS, 11 REVIEW, 866 FAIL.

## HR Decision Boundary

- PASS candidates are automatically placed in the R1 shortlist; no HR action controls are available.
- REVIEW candidates between the configured review and pass thresholds receive Move forward, Hold, and Reject controls.
- FAIL candidates are automatically rejected; no HR action controls are available.
- The API rejects attempts to apply HR actions to PASS or FAIL candidates.

## Outputs

- Shortlisted workbook: `storage/shortlisted/REQ-IT-SUPPORT-ENGINEER-001_20260622_031422.xlsx`
- Rejected workbook: `storage/rejected/REQ-IT-SUPPORT-ENGINEER-001_20260622_031422.xlsx`
- Distribution audit: `scripts/audit_validator_distribution.py`
- Runtime verifier: `scripts/verify_validator_batch.py`
- Reviewed batch runner: `scripts/run_excel_intake.py`

## Frontend Engineer Distribution Audit

- Batch: `95204649-5b2d-4472-90c3-97d0a7bce176`
- Requirement: Frontend Engineer, PASS 74+, REVIEW 59+, 2-6 years.
- Input: 1,000 synthetic simulation records.
- Observed distribution: 0 PASS, 0 REVIEW, 1,000 FAIL; minimum 2.99, average 31.62, maximum 56.40.
- Pool audit: zero records had a Frontend Engineer role. The top adjacent candidate matched only TypeScript and React while missing JavaScript, HTML, CSS, and REST APIs.
- Conclusion: score calculation was internally consistent, but the pool was unsuitable for evaluating this JD. The result is not valid as a production rejection decision.
- Remediation: the batch is `AUDIT_REQUIRED`, all imported applications are `VALIDATOR_AUDIT_REQUIRED`, and quarantined batches are excluded from HR and R1 operational views.
- Prevention: any batch of at least 20 candidates with no PASS or REVIEW result is automatically quarantined for a requirement/pool distribution audit.
- Verification: 34 backend tests passed and the Next.js production build passed.

### DevOps Recovery Verification

- Recovered batch: `b049e0ee-6a86-4cac-8d39-ce36df39bf50`.
- The backend completed all 1,000 records even though the original browser request was interrupted.
- Distribution: 41 PASS, 64 REVIEW, and 895 FAIL.
- The latest-batch endpoint returns the completed batch and allows the dashboard to recover without rerunning validation.

## Long-Running Intake Reliability

- The frontend now calls FastAPI directly instead of routing long validator requests through the Next.js rewrite proxy.
- FastAPI permits the local HireX frontend origins through explicit CORS configuration.
- Validator requests use a 15-minute client execution window.
- A batch is persisted as `RUNNING` before candidate processing begins, allowing recovery after a browser or network interruption.
- The dashboard retrieves the newest requirement batch and polls it to a terminal status after an interrupted request.
- Duplicate runs for the same requirement are rejected while a recent batch is running.
- A `RUNNING` batch older than 30 minutes is retired as `FAILED` so it cannot permanently lock a requirement.
- Verification: 34 backend tests passed and the Next.js production build passed.
