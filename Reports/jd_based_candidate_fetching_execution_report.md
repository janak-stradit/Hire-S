# HireX JD-Based Candidate Fetching Execution Report

## Objective
The goal was to stop fetching candidates by a fixed required count and instead fetch the maximum eligible candidates based on the job requirement. The new flow now uses JD criteria before validation, so candidates are filtered first and then passed to the validator.

## What Was Added
Added richer JD fetching criteria:

- Location preference
- Work mode
- Notice period limit
- Salary / CTC range
- Role title variants
- Must-have skills with minimum experience notes
- Preferred industry / domain
- Candidate freshness window
- Willing to relocate
- Source priority

## Backend Changes
Updated `hirex/excel_intake/contracts.py`:

- Added new fields to `JobRequirementRow`.
- Kept the model backward-compatible with older JD workbooks.

Updated `hirex/excel_intake/workbooks.py`:

- Added new JD columns to the default JD template.
- Updated default role requirements with fetching criteria.
- Replaced hardcoded Excel column positions with header-based lookup.
- Fixed status handling after column expansion.
- Upgraded `storage/job_requirements/jd_input.xlsx` from the old 19-column JD format to include the new fetch-criteria columns.
- Filled fetch criteria for the 10 existing default JD rows.

Updated `hirex/excel_intake/service.py`:

- Added `CandidateFetchCriteria`.
- Candidates are now checked against:
  - Role / role variants
  - Required skill match
  - Experience range
  - Location
  - Work mode
  - Salary range
  - Notice period
  - Freshness window
  - Preferred domain
- Only matching candidates are imported into the validator batch.
- Non-matching candidates are skipped before validation.
- Source priority is used for ordering candidates first, not for rejecting otherwise valid candidates.

Updated `hirex/services/talent_pool_service.py`:

- Reusable rejected-pool candidates now use the same JD-based filtering before re-screening.
- This keeps old rejected candidates and new source candidates aligned to the same rule set.
- Reusable candidates are also ordered by JD source priority where source metadata is available.

## Frontend Changes
Updated `frontend/src/screens/admin/OperationsDashboardPage.tsx`:

- Removed the manual `Required candidates` input.
- Validator run now means: fetch all eligible matching candidates.
- Added JD form fields for:
  - Work mode
  - Role title variants
  - Must-have skill experience
  - Preferred domain
  - Notice period
  - Freshness window
  - Relocation
  - Source priority
- Updated run confirmation text to show that candidates are selected by criteria, not by count.
- Added JD preview display for the new fetching criteria.

## What Was Removed
Removed the manual candidate count behavior from the HR dashboard.

Earlier:

`HR enters required candidate count -> system tries to process that count`

Now:

`HR selects JD + candidate source -> system fetches all candidates matching JD criteria -> validator scores them`

## Current Flow
1. HR creates or selects a JD.
2. JD contains role, skills, experience, location, work mode, salary, notice period, freshness, and other criteria.
3. HR selects candidate source.
4. HireX checks reusable talent pool first.
5. HireX checks source workbook candidates.
6. Candidates not matching JD fetching criteria are skipped before validation.
7. Matching candidates are passed to the validator.
8. Validator decides PASS, REVIEW, or FAIL.
9. Results are stored batch-wise in PostgreSQL and shown in the HR dashboard.

## Why This Is Stronger
This makes the system closer to real Naukri / LinkedIn sourcing. HR does not decide an artificial count first. The system fetches based on role fit, skill fit, location fit, experience fit, salary fit, notice period, and freshness. The validator then works on a cleaner and more relevant candidate set.

## Verification
Executed:

- `python -m compileall hirex`
- `pytest tests/test_excel_intake.py`
- `npm run lint`
- `npm run build`

Result:

- Backend compile passed.
- Excel intake test suite passed: 8 tests.
- Frontend lint passed.
- Next.js production build passed.
