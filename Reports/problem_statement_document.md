# HireX - Problem Statement Document

**Document purpose:** Define the real-world recruitment problem selected for HireX, its business impact, refined scope, proposed AI solution, and expected outcomes.

**Project:** HireX - AI-Powered Interview System  
**Domain:** HR Technology (HRTech) - Talent Acquisition and Recruitment Automation  
**Prepared for:** Mentor/lead review and project tracker documentation  

---

## 1. Problem Background

Recruitment teams often handle candidate sourcing, resume screening, HR screening, technical interviews, feedback collection, and final decision-making through separate tools and manual processes. Candidate information may come from LinkedIn, Naukri, resumes, Excel files, emails, referrals, or internal records, but it is not always stored in a structured and reusable way.

Because of this, recruiters spend a large amount of time filtering unsuitable candidates, coordinating multiple rounds, and manually comparing candidate profiles against job requirements. This slows down hiring and can cause inconsistent candidate evaluation.

---

## 2. Real-World Problem Identified

Many companies still conduct candidate screening, language checks, technical interviews, behavioral evaluation, interview honesty checks, and final hiring decisions as separate manual steps. These disconnected activities increase recruiter workload and make it difficult to maintain a consistent, evidence-based hiring process.

The problem becomes larger when companies receive hundreds or thousands of candidates for a role. Good candidates can be missed, unsuitable candidates can consume interview time, and rejected candidates are often not reused for future openings even if they may fit another role later.

---

## 3. Final Problem Statement

Develop an AI-based hiring system that helps companies automate candidate screening, conduct technical interviews, detect interview dishonesty, and generate hiring insights. The system aims to reduce recruiter workload, improve hiring quality, and accelerate the recruitment process while keeping final hiring decisions under HR control.

---

## 4. Problem Scope

The problem scope includes:

- Candidate intake from Excel, resume folders, sourced candidate lists, and future job portal integrations.
- Candidate deduplication so the same candidate is not stored repeatedly.
- Resume/profile parsing to extract skills, education, experience, projects, certifications, and summary.
- Job requirement matching using role, skills, experience, education, location, salary, and JD text.
- Pre-screen validation with PASS, REVIEW, and FAIL outcomes.
- HR review only for candidates in the middle review band.
- Storage of rejected and available candidates as reusable talent pool metadata.
- Periodic candidate profile refresh when updated source data is found.
- Evidence-based dashboards for HR and admin users.
- Future interview agents for screening, technical rounds, behavioral assessment, and integrity monitoring.

---

## 5. Out of Scope for Current MVP

The following items are part of the broader HireX architecture but are not the immediate MVP focus:

- Live LinkedIn/Naukri scraping integration.
- Full candidate self-service application portal.
- Real-time audio/video interview agent execution.
- Production-grade proctoring and identity verification.
- Offer management, onboarding, payroll, or employee lifecycle management.
- Final automated hiring decisions without HR approval.

---

## 6. Business Impact

| Business impact area | Expected improvement |
|----------------------|----------------------|
| Recruiter productivity | Reduces manual resume screening and repetitive candidate review effort. |
| Hiring speed | Shortlists suitable candidates faster using automated validation. |
| Candidate quality | Improves role matching through skills, experience, education, certifications, and JD-based scoring. |
| Evaluation consistency | Uses standardized scoring, reason codes, and evidence instead of only manual judgment. |
| Cost reduction | Reduces time spent on clearly unfit candidates and repeated screening cycles. |
| Talent reuse | Builds a reusable candidate database for future job openings. |
| Auditability | Maintains score breakdowns, reason codes, candidate timeline, batch history, and HR actions. |
| HR control | Keeps the final decision with HR while AI provides evidence and recommendations. |

---

## 7. Stakeholders

| Stakeholder | Need |
|-------------|------|
| Recruiter | Quickly identify suitable candidates and reduce manual screening effort. |
| HR manager | Review evidence, take final decisions, and track hiring pipeline status. |
| Technical interviewer | Receive role-aligned candidate context and structured evaluation support. |
| Hiring manager | Get better quality shortlisted candidates faster. |
| Candidate | Experience a faster, more organized hiring process. |
| Admin/team lead | Monitor batches, validator performance, pool quality, and system configuration. |

---

## 8. Current Process Issues

| Issue | Explanation |
|-------|-------------|
| High manual effort | Recruiters manually read resumes and compare them with job descriptions. |
| Inconsistent shortlisting | Candidate selection may depend on individual reviewer judgment. |
| Slow screening cycle | Resume review and interview coordination increase hiring turnaround time. |
| Fragmented data | Candidate information is not always stored in one clean database. |
| Duplicate candidates | Same candidate may appear across multiple sources or batches. |
| Weak rejected pool reuse | Rejected candidates are rarely organized for future role matching. |
| Limited explainability | It is difficult to justify why a candidate was shortlisted or rejected. |
| Candidate freshness risk | Candidate skills may change over time, but stored records may become stale. |

---

## 9. Proposed AI-Based Solution

HireX proposes an AI-powered recruitment automation system that receives candidate data, deduplicates profiles, parses candidate information, validates candidates against job requirements, and stores all results in a structured PostgreSQL database.

The system classifies candidates into:

- **PASS:** Candidate is automatically shortlisted for R1 screening.
- **REVIEW:** Candidate requires HR review because the score is in the middle threshold band.
- **FAIL:** Candidate is rejected for the current role but stored as reusable talent pool metadata for future openings.

The system also maintains candidate timeline, batch history, validator versioning, reason bank, refresh change detection, and pool analytics to make the hiring process explainable and auditable.

---

## 10. Proposed HireX Process Flow

```text
Candidate Sources
(Excel / Resumes / LinkedIn / Naukri / Existing Pool)
      |
      v
Candidate Intake and Deduplication
      |
      v
Job Requirement Selection
      |
      v
Pre-Screen Validator
      |
      +---- PASS ----> R1 Shortlist
      |
      +---- REVIEW --> HR Review
      |
      +---- FAIL ----> Reusable Talent Pool
      |
      v
PostgreSQL Storage and Audit Trail
      |
      v
R1 / T1 / T2 Agents and Dashboards
      |
      v
Final HR Decision
```

---

## 11. HireX MVP Functional Components

| Component | Purpose |
|-----------|---------|
| Candidate pool | Stores candidate data from Excel, resumes, or future sourcing integrations. |
| Job requirement input | Stores JD details such as role, experience, skills, education, salary, and thresholds. |
| Pre-screen validator | Scores candidates and classifies them as PASS, REVIEW, or FAIL. |
| PostgreSQL data layer | Stores users, profiles, resumes, jobs, applications, parsed data, validator results, and HR actions. |
| Batch tracking | Tracks each validator run by batch, role, counts, and outcomes. |
| Reusable talent pool | Reuses rejected/available candidates for future job openings. |
| Refresh detection | Detects updated candidate information from later sourcing cycles. |
| Reason bank | Stores structured reasons for rejection or HR decisions. |
| Validator versioning | Records which validator/parser/scoring version produced the result. |
| HR dashboard | Allows HR/admin users to review candidates, evidence, batches, and decisions. |

---

## 12. Success Criteria

The solution will be considered successful if it can:

- Process a large candidate pool against a selected job requirement.
- Deduplicate candidates across repeated batches.
- Produce PASS, REVIEW, and FAIL decisions with score evidence.
- Store candidate, application, validator, batch, and HR decision data in PostgreSQL.
- Reuse rejected candidates for future job openings.
- Detect changed candidate information during periodic refresh cycles.
- Show HR a clear dashboard with score breakdown, missing skills, reason codes, and candidate timeline.
- Keep final hiring control with HR for review-zone candidates.

---

## 13. Expected Outcome

The expected outcome is a recruitment automation platform that reduces manual screening time, improves candidate-job matching, provides explainable candidate evaluation, helps HR focus on high-potential or borderline candidates, and builds a reusable candidate database for future openings.

In the long-term architecture, HireX can extend this foundation into AI-based screening calls, technical interviews, behavioral evaluation, integrity monitoring, combined dashboards, master intelligence, and HR co-pilot recommendations.

---

## 14. Summary

The selected problem is important because recruitment is time-consuming, repetitive, and business-critical. HireX addresses this by combining structured candidate intake, AI-assisted validation, HR review workflows, reusable candidate metadata, refresh detection, and explainable dashboards. The system improves hiring speed and consistency while ensuring final decisions remain under HR control.

