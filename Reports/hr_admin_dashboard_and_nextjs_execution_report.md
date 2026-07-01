# HireX HR Operations Dashboard and Next.js Migration

Date: 2026-06-21

## Scope Completed

- Added an HR/recruiter/admin operations dashboard for all evaluated candidates.
- Added filters for PASS, REVIEW, and FAIL validator outcomes plus candidate search.
- Added candidate evidence view with score breakdown, validator explanation, skills, education, certifications, resume text, source, and verification metadata.
- Added HR actions: MOVE_FORWARD, HOLD, and REJECT.
- Added append-only `hr_review_actions` audit history with actor, reason, validator result, and timestamp.
- Added role-protected dashboard summary, list, detail, and decision APIs.
- Added a protected intake configuration preview with all saved JDs and real/synthetic pool counts.
- Added a dashboard JD form that upserts requirements into `storage/job_requirements/jd_input.xlsx`.
- Added an explicit confirmation workflow that runs the selected JD and candidate pool through Excel import, PostgreSQL persistence, validator scoring, and PASS/REVIEW/FAIL segregation.
- Real resumes are the default production pool; the 1,000-candidate synthetic pool is visibly marked simulation-only.
- Migrated the frontend from Vite and React Router to Next.js 16 App Router and React 19.
- Replaced the Vite API proxy with Next.js rewrites to FastAPI on port 8000.
- Applied Alembic migration `0004_hr_review` to PostgreSQL.

## Data Safety

- No Excel intake batch was executed.
- No real or synthetic candidate was passed to the validator.
- PostgreSQL audit after implementation:
  - intake batches: 0
  - validator results: 0
  - duplicate user emails: 0
  - duplicate candidate/job applications: 0
- All production candidate workbooks passed the workbook auditor.

## Verification

- Backend: 27 tests passed.
- Admin API tests cover authorization, summary, list, detail, score evidence, decision persistence, status transition, and audit history.
- Alembic upgrade and schema drift check passed on an isolated SQLite database.
- PostgreSQL migration completed successfully.
- Next.js production build passed with eight routes.
- ESLint passed.
- HTTP smoke checks returned 200 for `/operations` and `/login`.
- FastAPI `/health` returned `ok`.
- Protected configuration endpoint returned 401 without a token, confirming the authorization boundary.
- Live PostgreSQL remained at 0 intake batches and 0 validator results after verification.
- Public registration now always creates a candidate, even if a manager role is submitted.
- First manager creation is handled by the local password-prompting `scripts/bootstrap_manager.py` command.
- Final backend result: 28 tests passed.
- Created the first PostgreSQL admin account for `admin@hirex.com`; credentials were verified through the live login API.
- Removed candidate registration from the HR console and redirected `/register` to `/login` for the Excel-first MVP.
- Added JD status management for `active`, `draft`, and `inactive`; activating one JD automatically deactivates the prior active JD.
- Added a dedicated **Manage JDs** table showing every requirement with role, department, experience, thresholds, and an editable per-row status.
- Reworked requirement metrics into balanced threshold, experience, candidate-input, and processing-mode blocks.
- Added a persistent desktop sidebar hide/show control and expanded the dashboard to use the full available width.
- Verified the live catalog still contains 10 JDs with exactly one active JD.

## Cleanup

- Removed `storage/test_excel_intake` generated fixture data.
- Removed temporary SQLite databases, pytest cache, temporary test workspace, and project bytecode caches.
- Retained source tests, migrations, reports, workbooks, resumes, and operational storage directories.

## Known Notes

- The in-app visual browser could not start because of the local Windows sandbox, so screenshot-based visual QA was not available. Production compilation, lint, API tests, and HTTP smoke checks passed.
- npm reports two moderate PostCSS advisories inside the current Next.js dependency. npm's proposed forced fix downgrades to Next 9, so it was not applied. Track the upstream Next.js dependency update.
