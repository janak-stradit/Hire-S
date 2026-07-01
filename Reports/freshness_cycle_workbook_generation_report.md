# Freshness Cycle Workbook Generation Report

Generated at: 2026-06-23T07:52:42

## Purpose
Created staged sourcing workbooks to test HireX candidate identity dedupe, profile refresh, and 30-day freshness handling.

## Files
- `hirex_freshness_wave1_300_refreshed.xlsx`: 300 rows, 300 known, 0 new, missing cells 0, duplicate emails 0, duplicate candidate IDs 0, weak quality cells 0
- `hirex_freshness_wave2_200_refreshed_300_new.xlsx`: 500 rows, 200 known, 300 new, missing cells 0, duplicate emails 0, duplicate candidate IDs 0, weak quality cells 0
- `hirex_freshness_wave3_100_refreshed_200_new.xlsx`: 300 rows, 100 known, 200 new, missing cells 0, duplicate emails 0, duplicate candidate IDs 0, weak quality cells 0

## Overall Unique Candidate Count
- Base synthetic candidates: 1000
- New candidates added in wave 2: 300
- New candidates added in wave 3: 200
- Total unique candidate identities available after all waves: 1500

## Rich Content Quality Gate
- Required minimums: skills 45 chars, education 180 chars, certifications 200 chars, projects 1100 chars, summary 420 chars, raw_text/resume 2600 chars.
- All three generated workbooks passed the rich-content gate with zero weak quality cells.
