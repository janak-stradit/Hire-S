# HireX Resume Batch Excel Import Report

Generated: 2026-06-19

## Objective

Extract candidate information from the PDF/DOCX files in `HireX/Resumes`, map the information to the existing 43-column candidate spreadsheet contract, generate matching values only for missing fields, remove duplicates, and produce a complete workbook suitable for downstream agent verification.

## Output

- Master workbook: `Reports/hirex_candidate_master_with_extracted_resumes.xlsx`
- Reusable importer: `scripts/extract_resumes_to_hirex_excel.py`
- Untouched base workbook: `Reports/hirex_1000_candidate_dummy_data.xlsx`

The base workbook was not overwritten because Windows denied replacing it, most likely because it was open or locked. The validated result was saved as a separate master workbook.

## Resume Inventory

- Files found: 78
- PDF files: 72
- DOCX files: 6
- Unique candidates imported: 66
- Duplicate/alternate resume versions removed: 10
- Scanned resumes manually transcribed from the source image: 1
- Unusable unique resume groups: 0

## Rejected Non-Resume Files

The following files were reservation tickets, not resumes, and were excluded:

- `19679385.pdf`
- `19679385 (1).pdf`

## Candidate-Level Deduplication

Duplicate versions were detected through file hashes, extracted emails, phone numbers, and candidate identity. The richest usable resume version was retained for each candidate. Multiple versions were found for candidates including Pramod Deore, Rohit Ingle, Manish Shirsat, Ravindranath Vajire, and Yash Chatse.

## Mapping Rules

- Source resume values were used wherever present.
- `resume` and `raw_text` contain the same extracted source text.
- PDF/DOCX file metadata comes from the actual source file.
- Candidate, resume, and parsed-resume IDs are deterministic and unique.
- Missing narrative fields are visibly marked with `[Synthetic completion]`.
- Missing email addresses use the reserved `hirex-synthetic.example` domain.
- Missing phones, locations, expected salary, notice period, timestamps, links, application status, and IDs are deterministically generated.
- The original 43 columns were preserved without renaming or reordering.

## Synthetic Completion Counts

Among the 66 imported candidates:

- Email: 1
- Phone: 1
- Location: 18
- Current company: 35
- Highest education: 8
- Skills: 2
- Summary: 22
- Education details: 15
- Certifications: 42
- Projects: 40

Synthetic completion is used only where the source resume does not provide a usable value. The original extracted resume text remains unchanged for verification.

## Final Workbook Validation

- Original synthetic rows retained: 1,000
- Real candidate rows appended: 66
- Final data rows: 1,066
- Final columns: 43
- Blank required cells: 0
- Duplicate emails: 0
- Duplicate phones: 0
- Duplicate candidate IDs: 0
- Invalid candidate/upload/application timelines: 0
- Resume/raw-text mismatches: 0
- Resume cells exceeding Excel's 32,767-character limit: 0
- Ticket files present in workbook: 0
- Suspicious extracted names after correction: 0
- Excel table range: `A1:AQ1067`
- Frozen header: `A2`

## Source Fidelity Validation

- Selected source documents: 66
- Imported workbook documents: 66
- Missing source documents: 0
- Extracted source-text mismatches: 0
- Source fidelity: passed

## Quality Corrections

Ambiguous resumes were manually reviewed and corrected using their source content, including:

- Pooja Bhandare: Senior Quality Analyst / Testing
- Parikshit Sharma: Workforce Management Specialist / HR
- Rayavaram Gangadhara: Technical Support Engineer / IT Support
- Shriprasad Wable: Security Engineer / Cybersecurity
- Dhananjay Vilas Pandit: scanned resume manually transcribed

## Rendering Note

The dedicated spreadsheet renderer and LibreOffice were unavailable in the Windows sandbox. The final workbook was reopened and validated using workbook structure, styles, table metadata, row/column counts, content checks, source-document comparisons, and duplicate/completeness assertions.

## Overall Result

Passed.
