# Reusable Talent Pool Execution Report

## Implemented Flow

1. Ingest candidates from an authorized API, export, or workbook into one canonical profile.
2. Preserve every source sighting separately without duplicating the candidate.
3. Store parsed resume evidence once for future job matching.
4. Screen `AVAILABLE` database candidates against a new job before requesting external candidates.
5. Move PASS and REVIEW candidates to `IN_PROCESS`.
6. Return validator FAIL and HR-rejected candidates to `AVAILABLE`.
7. Release later-stage R1, T1, T2, managerial, or HR rejections through the talent-pool release API.
8. Report the remaining target shortfall before an authorized external batch is sourced.

## Data Model

- `candidate_profiles`: canonical candidate and current talent-pool state.
- `candidate_source_records`: LinkedIn, Naukri, authorized export, API, or other source sightings.
- `candidate_lifecycle_events`: auditable state transitions and rejection reasons.
- `applications`: one candidate-to-job relationship per opening.
- `validator_results`: immutable evaluation history for each job.
- `parsed_resumes`: reusable evidence used to re-score candidates without reparsing source files.

## Safeguards

- Email-based canonical identity prevents repeated candidate creation.
- Candidate plus job uniqueness prevents repeated applications for one opening.
- Synthetic candidates are excluded from production talent-pool screening.
- A lower-trust synthetic sighting cannot overwrite authorized source provenance.
- Direct job-board acquisition remains behind approved API/export adapters.

## Verification

- PostgreSQL upgraded through `0011_expand_verification`.
- Alembic drift check passed.
- 66 authorized profiles synchronized and parsed for pool-first screening.
- 35 backend tests passed.
- Next.js production build passed.

## Batch-Scoped Candidate Architecture

- Candidate identity is stored once in `candidate_profiles` and deduplicated by the canonical user email.
- Each job opening has its own `applications` relationship to that candidate.
- Each execution batch has one `candidate_batch_memberships` row per candidate.
- Validator evidence remains immutable and points to the exact batch through `validator_results.intake_batch_id`.
- HR and downstream R1/T1/T2/managerial/final-HR outcomes are recorded as batch-specific stage events.
- Rejection in one batch does not erase evidence or decisions from another batch.
- A candidate returns to the reusable pool only when no other active batch membership remains.
- The HR dashboard supports selecting an execution batch so counts, evidence, and HR actions remain isolated.

## Automatic Pool-First Behavior

- `Run validator` checks the selected pool mode first.
- With Synthetic selected, only previously rejected synthetic candidates are considered for simulation reuse.
- With Real selected, only authorized production candidates are considered.
- When reusable candidates exist, they are screened first and the same source workbook is not re-imported as a fake new cluster.
- When no reusable candidates exist, the selected external workbook becomes the first candidate cluster.
- A shortfall after pool screening is reported as an external sourcing requirement.

## Current Manual Batch

- Backend Engineer batch: `0b147ca2-ff7e-4fcd-a693-2d9da02c8057`.
- 1,000 candidates mapped to 1,000 batch memberships.
- 132 candidates are in HR review and 868 are rejected/reusable in synthetic simulation mode.
