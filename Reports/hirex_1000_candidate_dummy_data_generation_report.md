# HireX 1,000 Candidate Dummy Data Generation Report

Generated: 2026-06-19

## Request

Review and update the supplied dummy-data script so it generates 1,000 candidates while preserving the existing spreadsheet columns and adding rich, realistic resume content for every supported role/domain.

## Files

- Generator: `scripts/generate_hirex_1000_candidates.py`
- Workbook: `Reports/hirex_1000_candidate_dummy_data.xlsx`

## Preserved Column Contract

The existing 43 columns were preserved in the original order, from `candidate_id` through `resume`. No columns were removed, renamed, or reordered.

## Resume Content Added

Every candidate resume includes:

- Contact information and professional links
- Multi-sentence domain-specific professional summary
- Company name, role, employment dates, and time period
- Four quantified experience bullets per employment entry
- Domain-specific grouped skills
- Education with institution, timeline, and score/CGPA
- Two or three detailed projects with tools and achievement bullets
- Certifications with issue year and credential ID
- Selected achievements
- Notice period, salary expectation, preferred location, and languages

## Supported Domains

- Accounting
- Data Analytics
- Data Engineering
- DevOps
- Finance
- HR
- IT Support
- Sales and Marketing
- Software Development
- Testing

## Execution Results

- Candidates generated: 1,000
- Spreadsheet data rows: 1,000
- Spreadsheet columns: 43
- Duplicate emails: 0
- Duplicate phones: 0
- Duplicate candidate IDs: 0
- Blank resumes: 0
- Minimum resume length: 2,898 characters
- Average resume length: 3,945.55 characters
- Maximum resume length: 4,849 characters
- Resume cells exceeding Excel's 32,767-character limit: 0
- Resume/raw-text mismatches: 0
- Invalid application timelines: 0

## Saved Workbook Validation

- Sheet name: `candidates`
- Rows including header: 1,001
- Columns: 43
- Frozen pane: `A2`
- Excel table/filter: `HireXCandidates`
- Domain count: 10
- Header styling present: yes
- Required resume sections present in all records: yes
- Company names present in all resumes: yes
- Employment dates present in all resumes: yes
- Education scores present in all resumes: yes
- Project tool lists present in all resumes: yes
- At least 10 detailed bullets per resume: yes

## Rendering Note

The dedicated spreadsheet runtime and local LibreOffice renderer were unavailable in the Windows sandbox. The workbook was therefore generated with the supplied Python/Pandas approach and verified by reopening the final `.xlsx` and checking its structure, styling metadata, table/filter configuration, and all candidate content.

## Overall Result

Passed.
