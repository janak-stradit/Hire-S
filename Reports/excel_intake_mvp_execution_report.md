# HireX Excel Intake MVP Execution Report

Date: 2026-06-21

## Architecture Decision

Excel was implemented as an intake adapter only. PostgreSQL remains the system of record, and
the existing pre-screen validator remains the single screening engine. The future candidate
portal can write the same candidate, resume, job, and application records, so replacing Excel
with portal intake will not require changes to R1 or the downstream architecture.

## Implemented Flow

1. Read and validate the candidate pool workbook.
2. Read exactly one active job requirement.
3. Upsert the job, users, candidate profiles, resumes, and applications into PostgreSQL.
4. Preserve candidate source provenance and agent-processing permission.
5. Run the existing pre-screen validator with requirement-specific thresholds.
6. Store parsed resumes, parsed job descriptions, and validator results.
7. Route PASS to R1, REVIEW to HR review, and FAIL to rejection.
8. Export shortlist and rejection workbooks.
9. Persist an auditable Excel intake batch record.

## Storage Artifacts

- `storage/candidate_pool/hirex_candidates.xlsx`: 66 resume-extracted candidates; agent processing enabled.
- Optional synthetic test workbook: generated only with `--include-synthetic`; agent processing disabled.
- `storage/job_requirements/jd_input.xlsx`: formatted job requirement template; sample row remains `draft`.
- `storage/shortlisted/`: PASS and REVIEW exports.
- `storage/rejected/`: FAIL exports.
- `storage/intake_logs/`: reserved for operational intake logs.

## Database Changes

- Candidate provenance, verification status, source reference, and processing permission.
- Job requirement identifier, preferred skills, education, certifications, thresholds, and intake source.
- Application intake source and batch identifier.
- New `excel_intake_batches` audit table.
- Migration `0003_excel_intake` applied successfully to PostgreSQL database `HireX`.

## API and CLI

- `POST /api/excel-intake/run`
- `GET /api/excel-intake/batches/{batch_id}`
- `GET /api/validator/queues/r1`
- `python scripts/prepare_excel_mvp_storage.py`
- `python scripts/run_excel_intake.py`

## Safety Controls

- Intake paths must remain under `HireX/storage`.
- Only recruiter, HR, or admin users can run an intake batch.
- Synthetic candidates are excluded unless explicitly requested and remain marked test-only.
- Only candidates with `agent_processing_allowed=true` can appear in the R1 queue.
- Duplicate candidate emails and malformed workbook schemas stop the batch.
- Exactly one active/open requirement is required.
- Resume source text from the workbook is passed to the validator, avoiding lossy PDF re-extraction.

## Verification

- Test suite: 17 passed.
- Ruff checks for changed modules: passed.
- Python compilation: passed.
- Alembic schema drift check: passed; no new upgrade operations detected.
- Real candidate workbook: 66 data rows, 47 columns, zero duplicate emails.
- Synthetic workbook: 1,000 data rows, 47 columns, zero duplicate emails.
- Real source type set: `resume_extracted`; processing flag set: `true`.
- Synthetic source type set: `synthetic`; processing flag set: `false`.
- Workbooks contain named tables, filters, frozen headers, controlled widths, and job-status validation.

## Intentional Pending Action

No real screening batch was executed because a genuine job requirement was not supplied. HR must
fill the JD template and change exactly one row to `active`; running the CLI or API will then import,
validate, route, and export candidates end to end.
