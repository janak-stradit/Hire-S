# HireX Workbook Quality Audit Report

Date: 2026-06-21

## Issue Corrected

The `created_at` cells in `jd_input.xlsx` were stored as Excel date-time values. VS Code's Excel
viewer displayed the underlying serial value, such as `46194.40`, instead of the formatted date.

The JD generator now writes ISO-8601 UTC text such as `2026-06-21T09:33:21Z` and explicitly applies
the Excel text format. This is stable across VS Code, Microsoft Excel, LibreOffice, and API readers.

## Files Audited

1. `Reports/hirex_candidate_master_with_extracted_resumes.xlsx`
   - 1,066 candidate rows.
   - 43 columns.
   - Result: PASS.
2. `storage/candidate_pool/hirex_candidates.xlsx`
   - 66 production candidate rows.
   - 47 columns.
   - Result: PASS.
3. `storage/job_requirements/jd_input.xlsx`
   - 10 job requirement rows.
   - 19 columns.
   - Result: PASS.
4. `storage/candidate_pool/test_synthetic_candidates.xlsx`
   - 1,000 synthetic simulation rows.
   - 47 columns.
   - Result: PASS after explicit regeneration.

## Checks Passed

- Unique and nonblank headers.
- Expected workbook schemas.
- Duplicate candidate, resume, parsed-resume, email, phone, and requirement identifiers.
- Blank resume source text.
- Resume and raw-text fidelity.
- Formula error markers.
- Candidate provenance and agent-processing flags.
- Resume source-file existence.
- Experience and salary ranges.
- PASS and REVIEW threshold ordering and bounds.
- Exactly one active requirement.
- Named table ranges, filters, and frozen headers.
- ISO-8601 JD creation timestamps.

## Intentional Data Characteristics

- The historical master workbook contains 1,000 synthetic and 66 resume-extracted candidates.
- The production candidate pool contains only the 66 resume-extracted candidates. The separate
  synthetic workbook is used only when simulation is explicitly enabled.
- Some structured fields for the real candidates contain visibly marked synthetic completion where
  the source resume did not provide a value. Resume `raw_text` remains the verification source.
- The historical master uses a filtered range rather than a named Excel table; this does not affect
  ingestion because the production pool has the named `HireXCandidates` table.

## Repeatable Preflight

Run before any screening batch or after modifying a workbook:

`python scripts/audit_hirex_workbooks.py`

The command exits with a failure status and lists affected cells or rows when an anomaly is detected.
