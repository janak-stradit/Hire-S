# HireX Candidate Pool, Freshness, and Sourcing Scraping Case Study Report

## 1. What Was Implemented

This update improves the candidate sourcing side of HireX. The system now supports richer candidate pool inputs, 30-day profile freshness, automatic JD requirement IDs, and a practical sourcing strategy for LinkedIn, Naukri, and Indeed.

## 2. Synthetic Candidate Excel Updates

Updated the synthetic candidate workbooks with the required sourcing factors:

- `preferred_work_mode`
- `willing_to_relocate`
- `preferred_locations`
- `industry_domain`
- `profile_last_updated_at`
- `profile_refresh_cycle_days`

The `profile_refresh_cycle_days` value is set to `30` for the synthetic pool and all freshness-cycle workbooks.

Updated files:

- `storage/candidate_pool/test_synthetic_candidates.xlsx`
- `storage/candidate_pool/freshness_cycles/hirex_freshness_wave1_300_refreshed.xlsx`
- `storage/candidate_pool/freshness_cycles/hirex_freshness_wave2_200_refreshed_300_new.xlsx`
- `storage/candidate_pool/freshness_cycles/hirex_freshness_wave3_100_refreshed_200_new.xlsx`

Each file now has 53 columns.

## 3. Candidate Pool Options Added

The HR dashboard candidate pool dropdown now includes:

- Extracted real resumes
- Synthetic simulation pool
- Freshness wave 1 - 300 refreshed
- Freshness wave 2 - 200 refreshed + 300 new
- Freshness wave 3 - 100 refreshed + 200 new

Backend change:

- `hirex/excel_intake/service.py`
- `hirex/api/excel_intake/routes.py`

Frontend change:

- `frontend/src/screens/admin/OperationsDashboardPage.tsx`

## 4. 30-Day Periodic Freshness Cycle

HireX already had a 30-day freshness rule in the database path. This update made it explicit from the candidate workbook also.

Current freshness behavior:

1. Candidate has `profile_last_updated_at`.
2. Candidate has `profile_refresh_cycle_days = 30`.
3. HireX stores `profile_last_refreshed_at`.
4. HireX calculates `profile_refresh_due_at = profile_last_updated_at + 30 days`.
5. Candidate becomes stale when the due date is crossed.
6. Stale candidates should be refreshed from source before being reused for another opening.

## 5. Automatic Requirement ID

Earlier, HR had to enter `requirement_id` manually.

Now:

- HR enters the role.
- HireX auto-generates the requirement ID.
- Example: `Data Engineer` becomes `REQ-DATA-ENGINEER-001`.
- If the ID already exists, the next number is used.

This reduces manual errors and keeps JD IDs consistent.

## 6. Scraping Case Study

### Main Finding

For our HireX use case, scraping should not be treated as only a technical task. Candidate profile data is personal data, and job platforms have strict access rules. The best production approach is:

1. Use official recruiter exports, ATS integrations, or approved APIs where available.
2. Use a sourcing adapter to convert platform data into the HireX candidate Excel/schema.
3. Use AI extraction only after data access is permitted.
4. Store candidate identity once and refresh profile data every 30 days.

### LinkedIn

LinkedIn is not a good target for raw scraping.

Reason:

- LinkedIn user agreement restricts unauthorized automated methods.
- Their terms mention bots and unauthorized automation in the platform restrictions.

Recommended approach:

- Use LinkedIn Recruiter exports or approved integration routes.
- Do not build a browser bot that logs in and scrapes profiles.

Source:

- LinkedIn User Agreement: https://www.linkedin.com/legal/user-agreement

### Indeed

Indeed is also not a good target for raw scraping.

Reason:

- Indeed terms restrict automated access, data mining, scraping, and bulk automated activity without permission.
- Indeed also mentions Smart Sourcing and recruiter-side responsibility for use of candidate data.

Recommended approach:

- Use Indeed employer dashboard/export/API/integration if available.
- Do not bypass Smart Sourcing/contact rules with a scraper.

Source:

- Indeed Terms: https://www.indeed.com/legal

### Naukri

Naukri should be handled carefully.

Recommended approach:

- Verify Resdex/Naukri recruiter account terms.
- Prefer official recruiter exports, Resdex access, or approved partner/API access.
- Do not assume public scraping is allowed until terms are confirmed from the recruiter account or official agreement.

## 7. ScrapeGraphAI Review

Repository checked:

- https://github.com/ScrapeGraphAI/Scrapegraph-ai

What it is useful for:

- AI-based structured extraction from pages or local documents.
- It supports `SmartScraperGraph`, where we provide a prompt and source URL.
- It can extract structured data into JSON-like output.
- It supports multiple LLM backends.

Important limitation:

- ScrapeGraphAI solves extraction, not platform permission.
- It should not be used to bypass LinkedIn/Indeed/Naukri access rules.

Best HireX usage:

- Use it as an extraction layer after legally obtaining candidate pages/files/exports.
- Good for:
  - Parsing exported HTML
  - Parsing allowed profile pages
  - Normalizing job board exports
  - Extracting candidate fields into HireX schema

Not recommended:

- Direct login scraping of LinkedIn/Indeed/Naukri without permission.

## 8. Script or Scraping Agent?

For MVP:

- A script is enough.
- It can read approved exports or Excel/CSV files and map them to HireX schema.

For production:

- Use a sourcing agent.
- The agent should not blindly scrape.
- It should manage:
  - Source permissions
  - Rate limits
  - Export imports
  - Duplicate identity matching
  - 30-day refresh checks
  - Data completeness validation
  - Audit logs

Recommended architecture:

`Platform Export / Approved API -> Sourcing Adapter -> AI Extraction -> Candidate Schema Validation -> Candidate Identity Dedupe -> Talent Pool -> Validator`

## 9. Final Recommendation

Use scripts for the current practical version and design a future sourcing agent.

The sourcing agent should not be an illegal scraper. It should be a controlled ingestion system that uses approved platform data, refreshes candidate profiles every 30 days, and feeds clean candidate records into HireX.

## 10. Verification

Executed:

- `python -m compileall hirex`
- `pytest tests/test_excel_intake.py`
- `npm run lint`
- `npm run build`

Result:

- Backend compile passed.
- Excel intake tests passed: 8 tests.
- Frontend lint passed.
- Next.js production build passed.
