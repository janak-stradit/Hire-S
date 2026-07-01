# HireX - Batches, Rejected Pool, Freshness, and Intelligence Modules

**Document purpose:** Explain what has been implemented so far for batch-based candidate processing, rejected candidate reuse, candidate freshness updates, and the 8 intelligence add-ons.

**Project:** HireX - AI-Powered Interview System  
**Domain:** HRTech - Talent Acquisition and Recruitment Automation  
**Status:** Implemented in MVP foundation for validator, batch tracking, reusable talent pool, HR dashboard, freshness metadata, and intelligence/audit support.

---

## 1. Why These Changes Were Needed

Initially, HireX was focused on reading candidate data, running the validator, and showing PASS, REVIEW, and FAIL results. After further discussion, the flow was improved so rejected candidates are not wasted. Instead, they are stored as reusable candidate metadata and can be checked again for future job openings.

This makes HireX stronger because every validator run now contributes to a long-term candidate database. The system does not only process one job at a time; it keeps learning from batches, rejected candidates, HR decisions, and profile updates.

---

## 2. Batch-Based Processing

Every time HR/admin runs the validator for a job requirement, HireX creates a separate execution batch. A batch represents one complete validator run for a selected job role and candidate source.

Each batch stores:

- Batch ID
- Job requirement ID
- Job role
- Candidate source
- Number of candidates read
- Number of candidates imported
- Number of candidates skipped
- PASS count
- REVIEW count
- FAIL count
- Batch status
- Start and completion time

This allows HR to view results batch-wise instead of mixing all candidates from all previous runs together.

---

## 3. Why Batch View Is Important

Batch tracking is important because HR may run different roles at different times. For example:

- Batch 1: Backend Engineer
- Batch 2: AI Engineer
- Batch 3: Data Analyst

Each batch has its own shortlisted, review, held, and rejected candidates. Without batch tracking, all candidate counts get mixed and HR cannot know which candidates belong to which run.

Now HireX can show candidates according to a selected batch, so the dashboard becomes cleaner and easier to manage.

---

## 4. Rejected Candidate Pool Logic

Earlier, rejected candidates were simply treated as failed candidates for one role. Now, rejected candidates are stored as reusable talent pool candidates.

The meaning is:

- If a candidate fails for AI Engineer, they may still be useful for Data Analyst.
- If a candidate is rejected after R1 for Backend Engineer, they may still be useful for another future role.
- If the same candidate comes again in a new batch, HireX does not create duplicate records.

Instead, HireX keeps one master candidate profile and connects that candidate to multiple batches, jobs, validator results, and HR decisions.

---

## 5. Reusable Pool Flow

```text
New Job Requirement
        |
        v
Check Existing Reusable Candidate Pool
        |
        v
If enough candidates exist -> use pool candidates first
        |
        v
If not enough -> source new candidates from Excel / resumes / future portals
        |
        v
Deduplicate candidates
        |
        v
Run validator for selected job
        |
        v
PASS -> R1 Shortlist
REVIEW -> HR Review
FAIL -> Reusable Talent Pool
```

---

## 6. Duplicate Prevention

HireX avoids duplicate candidate records using candidate identity matching.

The system checks identifiers such as:

- Email
- Phone
- LinkedIn URL
- Source reference
- Resume/source metadata

If the candidate already exists, HireX updates the existing candidate profile and attaches the candidate to the new batch. It does not create a new duplicate candidate.

---

## 7. HR Decisions and Rejected Pool

The rejected pool is not only for validator FAIL candidates.

Candidates can enter the reusable pool from multiple points:

- Validator FAIL
- HR rejects a REVIEW candidate
- R1 rejects a shortlisted candidate
- Future T1/T2/HR gates reject a candidate

This means every rejection is stored with context, reason, batch, job, and candidate timeline. The candidate can still be reused later if another job requirement matches better.

---

## 8. Candidate Freshness / Periodic Update

The lead raised one important concern: candidate data may become old. A candidate rejected today may learn new skills after 30 days and update their profile on LinkedIn, Naukri, or another source.

To handle this, HireX now has candidate freshness logic.

Each candidate profile has:

- Last refreshed date
- Next refresh due date
- Freshness status
- Source record
- Refresh change history

This helps HireX know when a candidate profile should be checked again.

---

## 9. Freshness Update Flow

```text
Candidate found again from source
        |
        v
Identify candidate using email / phone / LinkedIn / source data
        |
        v
Check if candidate already exists
        |
        v
Compare old profile with new source data
        |
        v
If changes found:
    update profile
    store changed fields
    create refresh change record
    add candidate timeline event

If no changes found:
    update last seen date
```

---

## 10. What Counts as Freshness Change

Freshness changes can include updates in:

- Skills
- Current role
- Current company
- Experience
- Education
- Certifications
- Projects
- Resume/profile summary
- Source metadata
- Availability or processing permission

The goal is to make sure HireX does not use old candidate data when processing future openings.

---

## 11. Sourcing Batch Model

Apart from validator batch, HireX now also tracks sourcing batches.

A sourcing batch tells where the candidate group came from, for example:

- Excel candidate pool
- Synthetic candidate file
- Real resume folder
- Future LinkedIn/Naukri source
- Existing reusable pool

It stores:

- Source type
- Source reference
- Total candidates
- Known candidates
- New candidates
- Refreshed candidates
- Metadata

This helps explain how candidate data entered the system.

---

## 12. The 8 Intelligence Modules Added

We added the following 8 intelligence modules around the existing validator and dashboard flow.

| Module | What it does |
|--------|--------------|
| Candidate master timeline | Tracks important candidate events like validation, HR decision, refresh, and stage movement. |
| Refresh change detection | Detects what changed when a known candidate appears again with updated data. |
| Validator/scoring versioning | Stores validator version, parser version, scoring config version, and decision policy version for every result. |
| Pool analytics dashboard | Shows talent pool status, source mix, rejection reasons, and batch outcome patterns. |
| Sourcing batch model | Tracks where candidate groups came from and how many were new, known, or refreshed. |
| Reason bank for rejections | Stores structured reason codes for validator and HR rejection decisions. |
| Pool analytics | Helps understand reusable pool quality and rejected candidate trends. |
| Validator versioning | Makes validator decisions audit-ready and easier to debug in future changes. |

---

## 13. Candidate Master Timeline

The candidate timeline records important events during the candidate journey.

Examples:

- Candidate imported
- Validator decision created
- Candidate moved to R1 shortlist
- HR moved candidate forward
- HR held candidate
- HR rejected candidate
- Candidate profile refreshed
- Candidate moved to reusable pool

This gives HR and admin users a clear history of what happened with each candidate.

---

## 14. Reason Bank for Rejections

Reason bank gives structured rejection reasons instead of only free text.

Examples:

- Skill gap
- Experience mismatch
- Education mismatch
- Certification gap
- Low keyword relevance
- Borderline score
- Location mismatch
- Compensation mismatch
- Refresh required
- Not role aligned

This makes rejection analysis easier and helps HR understand common failure patterns.

---

## 15. Validator Versioning

Validator versioning stores which logic was used when the candidate was evaluated.

For each validator result, HireX stores:

- Validator version
- Resume parser version
- Scoring config version
- Decision policy version
- Scoring metadata

This is important because the validator will keep improving. If scoring changes later, we can still know which version created an older result.

---

## 16. Pool Analytics

Pool analytics helps HR/admin understand the overall candidate pool.

It can show:

- How many candidates are available
- How many are in process
- How many need refresh
- Source mix
- Top rejection reasons
- Batch outcome distribution

This turns rejected candidate data into useful hiring intelligence.

---

## 17. What We Have Implemented Now

Implemented so far:

- Batch-based validator execution
- Batch-wise dashboard filtering
- Candidate deduplication
- Candidate reusable pool
- Stage decision tracking
- HR review actions for REVIEW candidates
- Automatic PASS and FAIL handling
- Candidate freshness fields
- Refresh change records
- Sourcing batch tracking
- Candidate timeline
- Reason bank
- Validator versioning
- Pool analytics API and dashboard section
- Batch delete cleanup logic
- Tests for talent pool and batch workflows

---

## 18. What Will Come Next

Future planned additions:

- Real LinkedIn/Naukri/company portal sourcing
- Automatic 30-day refresh scheduler
- R1 screening and behavioral agent
- T1 technical adaptive agent
- T2 advanced technical agent
- D1 integrity monitor
- M1 master intelligence engine
- HR co-pilot
- More advanced analytics dashboards

---

## 19. Simple Explanation for Lead

We improved HireX so every validator run is stored as a batch, and candidates are tracked batch-wise instead of mixing all results together. Rejected candidates are no longer wasted; they are stored in a reusable talent pool and can be checked again for future job openings.

We also added candidate freshness logic so if a candidate later learns new skills or updates their profile, HireX can detect the change and update the existing candidate record instead of creating duplicates. Along with this, we added timeline, reason bank, validator versioning, sourcing batch, and pool analytics to make the system more explainable and ready for future R1/T1/T2 workflows.

---

## 20. Summary

The batch, rejected pool, freshness, and intelligence modules make HireX stronger than a simple one-time validator. The system now builds a reusable candidate database, tracks every process by batch, prevents duplicates, updates candidate information over time, and gives HR explainable data for better hiring decisions.

