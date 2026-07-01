# HireX - Current Process Flow Diagram

**Document purpose:** Document the existing as-is recruitment workflow before HireX AI automation.

**Project:** HireX - AI-Powered Interview System  
**Domain:** HR Technology (HRTech) - Talent Acquisition and Recruitment Automation

---

## 1. Current As-Is Process Flow

```text
Job Requirement Received
        |
        v
Candidate Sourcing
(LinkedIn / Naukri / Referrals / Emails / Portals)
        |
        v
Resume Collection
        |
        v
Manual Resume Screening
        |
        v
HR Screening Call
        |
        v
Technical Interview Round
        |
        v
Feedback and Evaluation
        |
        v
Final HR / Hiring Manager Decision
        |
        v
Select / Hold / Reject
```

---

## 2. Mermaid Flow Diagram

```mermaid
flowchart TD
    A[Job Requirement Received] --> B[Candidate Sourcing]
    B --> C[Resume Collection]
    C --> D[Manual Resume Screening]
    D --> E[HR Screening Call]
    E --> F[Technical Interview Round]
    F --> G[Feedback and Evaluation]
    G --> H[Final HR / Hiring Manager Decision]
    H --> I[Select]
    H --> J[Hold]
    H --> K[Reject]
```

---

## 3. Process Summary

The current recruitment process begins with receiving a job requirement, sourcing candidates, collecting resumes, manually screening profiles, conducting HR and technical interviews, and then making a final hiring decision. Most steps are handled manually or through separate tools, which increases recruiter workload, slows down hiring, and creates inconsistent candidate evaluation.
