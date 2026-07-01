# HireX End-to-End Workflow Guide for Project Lead

Date: 2026-06-21

## 1. Current MVP Entry Point

HireX currently uses Excel as the candidate and job-requirement intake adapter. Excel is not the
system of record. PostgreSQL is the system of record, and the same downstream workflow will remain
when the candidate portal is enabled later.

## 2. Candidate Source Preparation

The production candidate pool is stored at
`storage/candidate_pool/hirex_candidates.xlsx`. It contains 66 deduplicated candidates extracted
from real resume files. Synthetic candidates are not present in the production pool.

Every candidate includes provenance fields:

- `source_type`
- `verification_status`
- `source_reference`
- `agent_processing_allowed`

Only candidates with `agent_processing_allowed=true` may enter an agent queue.

## 3. Job Requirement Entry

HR maintains `storage/job_requirements/jd_input.xlsx`. The workbook currently contains nine role
requirements. Exactly one row must be `active`; the remaining rows must be `draft` or `closed`.

The active role is IT Support Engineer with thresholds 72/58. Each role contains required skills,
preferred skills, education, experience, salary range, location, employment type, JD text, and
screening thresholds.

## 4. Intake Preflight Validation

Before database writes, HireX checks:

- Both workbooks exist under `HireX/storage`.
- Required columns are present and unique.
- Exactly one job requirement is active.
- Experience, salary, and threshold ranges are valid.
- Candidate emails are present and unique.
- Candidate resume text is available.
- Candidate provenance allows agent processing.
- Synthetic data is excluded unless explicitly enabled for testing.

Any structural failure stops the batch before screening.

## 5. PostgreSQL Import

HireX creates an `excel_intake_batches` audit record and then imports data in this order:

1. Insert or update the active `jobs` record using stable `requirement_id`.
2. Insert or update candidate accounts in `users`, deduplicated by normalized email.
3. Insert or update personal and provenance data in `candidate_profiles`.
4. Store resume metadata in `resumes`.
5. Create one `applications` record connecting each eligible candidate to the active job.
6. Mark imported applications as `IMPORTED` with the Excel batch identifier.

Rerunning the same requirement updates existing records instead of creating duplicate candidates
or candidate/job applications.

## 6. Resume and JD Understanding

The validator parses the candidate's source resume text and the active JD. It uses the compiled
HireX talent taxonomy containing:

- 1,681 canonical skills.
- 311 aliases.
- 1,043 role strategies.
- 48 skill profiles.

Aliases normalize different spellings to the same skill. Longest-match handling prevents composite
skills such as `Apache Kafka` from also being counted as generic `Kafka`.

Required skills remain controlled by HR. Taxonomy role keywords enrich preferred matching but do
not silently become mandatory requirements.

## 7. Candidate Scoring

The default weighted final score is:

- Required skill match: 40%.
- Experience match: 25%.
- Education match: 10%.
- Mandatory certification match: 10%.
- Resume/JD keyword relevance and preferred skills: 15%.

The component scores, final score, explanation, parsed resume, and parsed JD are stored in
`parsed_resumes`, `parsed_job_descriptions`, and `validator_results`.

## 8. Threshold Decision

For the active IT Support Engineer role:

- Final score 72 or higher: `PASS` and `R1 Queue`.
- Final score from 58 through 71.99: `REVIEW` and `HR Review Queue`.
- Final score below 58: `FAIL` and `Auto Reject Queue`.

Each job may define different pass and review thresholds.

## 9. Outputs

PASS and REVIEW records are exported to `storage/shortlisted`. FAIL records are exported to
`storage/rejected`. PostgreSQL remains authoritative; workbooks are operational exports for HR.

The R1 candidate queue is available through `GET /api/validator/queues/r1`, optionally filtered by
`job_id`. It returns only the latest validator result and only candidates permitted for agent use.

## 10. R1 Screening Agent Boundary

The intake pipeline prepares and exposes the R1 queue, but the actual R1 calling/behavioral agent
is the next implementation phase. That agent will:

1. Fetch PASS candidates from the R1 queue.
2. Verify contact and scheduling eligibility.
3. Conduct the screening call.
4. Ask personal, role-alignment, project, experience, communication, behavioral, and compensation questions.
5. Store transcript, score, strengths, weaknesses, and go/no-go recommendation.
6. Present results to HR through the R1 dashboard and HR Gate 1.

## 11. Future Candidate Portal

The portal will replace only the Excel candidate-intake step. It will create the same `users`,
`candidate_profiles`, `resumes`, and `applications` records. The validator, taxonomy, thresholds,
PostgreSQL tables, queue routing, R1 agent, and later interview stages will remain unchanged.

The future unified flow is:

`Candidate Portal / Excel / Job Board Adapter -> PostgreSQL -> Validator -> R1 Queue -> R1 Agent -> HR Review -> Technical Interview Stages`

## 12. Operational Commands

Prepare the real candidate pool and JD workbook:

`python scripts/prepare_excel_mvp_storage.py`

Run an Excel screening batch:

`python scripts/run_excel_intake.py`

Rebuild role and skill knowledge after source changes:

`python scripts/build_talent_taxonomy.py`

Synthetic load-test data is generated only when explicitly requested:

`python scripts/prepare_excel_mvp_storage.py --include-synthetic`

## 13. Current Completion Status

Implemented:

- PostgreSQL foundation and migrations.
- Candidate, resume, job, and application models.
- Excel candidate/JD intake.
- Provenance and synthetic-data controls.
- Deduplication and idempotent imports.
- Resume/JD parsing and comprehensive taxonomy.
- Weighted validator scoring.
- PASS/REVIEW/FAIL routing.
- Shortlist/rejection exports.
- R1 queue API.
- Automated regression tests and execution reports.

Next phase:

- R1 screening/calling agent.
- Interview scheduling and retry policy.
- Transcript and behavioral scoring persistence.
- R1 dashboard and HR Gate 1 workflow.
