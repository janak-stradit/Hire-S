# HireX - Workflow and Architecture Diagrams

**Document purpose:** Explain the HireX process flow using PlantUML diagrams, covering both the currently implemented MVP workflow and the complete planned architecture.

**Project:** HireX - AI-Powered Interview System  
**Domain:** HRTech - Talent Acquisition and Recruitment Automation  
**Status:** MVP implemented for candidate intake, validator, batches, reusable pool, HR dashboard, reason bank, validator versioning, and refresh metadata. Future phases will extend this into R1, T1, T2, integrity monitoring, M1 intelligence, and HR co-pilot.

---

## 1. Current Implemented MVP Flow

This diagram shows the flow that is currently implemented in the project. Candidate data comes from Excel/source files, a job requirement is selected, the validator runs, results are stored in PostgreSQL, and HR can review candidates from the dashboard.

```plantuml
@startuml
title HireX Current MVP Flow - Candidate Intake to Validator Result

start

:HR/Admin selects Job Requirement;
:Select Candidate Pool\n(Synthetic / Real Resume / Existing Pool);
:Run Validator;

:Read Candidate Data;
:Deduplicate Candidate;
:Create or Update Candidate Profile;
:Parse Resume / Candidate Fields;
:Match Candidate with JD;
:Calculate Validator Score;

if (Score >= PASS threshold?) then (Yes)
  :Decision = PASS;
  :Move Candidate to R1 Shortlist;
elseif (Score >= REVIEW threshold?) then (Yes)
  :Decision = REVIEW;
  :Send Candidate to HR Review;
else (No)
  :Decision = FAIL;
  :Store Candidate in Reusable Talent Pool;
endif

:Store Result in PostgreSQL;
:Store Batch Summary;
:Store Reason Codes and Score Breakdown;
:Show Candidate in HR Operations Dashboard;

stop
@enduml
```

---

## 2. Current MVP Components Implemented

| Component | Status | Purpose |
|-----------|--------|---------|
| Candidate Excel/source intake | Implemented | Reads candidate data for validation. |
| Job requirement input | Implemented | Stores JD, role, skills, experience, salary, and thresholds. |
| Candidate deduplication | Implemented | Avoids storing same candidate again and again. |
| Pre-screen validator | Implemented | Scores candidates and classifies them as PASS, REVIEW, or FAIL. |
| Batch tracking | Implemented | Tracks every validator execution by batch. |
| HR operations dashboard | Implemented | Shows candidates, scores, status, and evidence. |
| Reusable talent pool | Implemented | Stores rejected/available candidates for future roles. |
| Candidate refresh metadata | Implemented | Tracks updated candidate profile changes. |
| Reason bank | Implemented | Stores structured rejection/HR decision reasons. |
| Validator versioning | Implemented | Stores validator, parser, scoring, and policy versions. |

---

## 3. Complete Planned HireX Hiring Flow

This is the complete planned HireX process based on the architecture. It includes the current validator flow plus future R1, T1, T2, HR gates, integrity monitoring, M1 intelligence engine, and HR co-pilot.

```plantuml
@startuml
title HireX Complete Planned Hiring Workflow

start

:Candidate Sources\n(Excel / Resume Folder / LinkedIn / Naukri / Company Portal / Existing Pool);
:Candidate Intake + Deduplication;
:Candidate Profile + Resume Parsing;
:Job Requirement Selection;
:Pre-Screen Validator;

if (Validator Decision?) then (PASS)
  :Move to R1 Shortlist;
elseif (REVIEW)
  :HR Gate 1 Review;
  if (HR Gate 1 Decision?) then (Move Forward)
    :Move to R1 Shortlist;
  elseif (Hold)
    :Candidate Held;
    stop
  else (Reject)
    :Store in Reusable Talent Pool;
    stop
  endif
else (FAIL)
  :Store in Reusable Talent Pool;
  stop
endif

:R1 Screening + Behavioral Agent;
:Generate R1 Score, Transcript,\nStrengths, Weaknesses, Go/No-Go;
:R1 Dashboard;

if (R1 Auto Threshold?) then (Shortlist)
  :Move to HR Gate 1 / T1;
elseif (Review)
  :HR Gate 1 Review;
else (Reject)
  :Store in Reusable Talent Pool;
  stop
endif

:T1 Technical + Adaptive Agent;
:Generate T1 Score, Transcript,\nSkill Coverage, Question Analysis;
:T1 Dashboard;

:Combined Dashboard\n(R1 + T1 + Integrity);
:HR Gate 2 Review;

if (HR Gate 2 Decision?) then (Move to T2)
  :T2 Technical + Adaptive Agent;
elseif (Optional T2)
  :T2 Technical + Adaptive Agent;
else (Reject)
  :Store in Reusable Talent Pool;
  stop
endif

:Generate T2 Score, Transcript,\nAdvanced Technical Evaluation;
:HR Gate 3 Final Decision;

if (Final Decision?) then (Select)
  :Candidate Selected;
elseif (Hold)
  :Candidate Held;
else (Reject)
  :Store in Reusable Talent Pool;
endif

stop
@enduml
```

---

## 4. Reusable Talent Pool and Future Opening Flow

This flow explains the lead's updated approach. Rejected candidates are not simply lost. They are stored once in the candidate database and reused for future job openings.

```plantuml
@startuml
title HireX Reusable Talent Pool Flow

start

:New Job Opening Created;
:Check Existing Reusable Talent Pool First;

if (Enough Candidates Available?) then (Yes)
  :Use Existing Pool Candidates;
else (No)
  :Use Existing Pool Candidates;
  :Source Additional Candidates\nfrom LinkedIn / Naukri / Excel / Resumes;
endif

:Deduplicate Candidates;

if (Candidate Already Exists?) then (Yes)
  :Update Existing Candidate Metadata;
  :Attach Candidate to New Batch;
else (No)
  :Create New Candidate Profile;
  :Attach Candidate to Batch;
endif

:Run Validator for Selected Job;

if (Candidate Passes?) then (PASS)
  :Move to R1 Shortlist;
elseif (Needs HR Review?) then (REVIEW)
  :Move to HR Review;
else (FAIL)
  :Keep Candidate Available\nfor Future Openings;
endif

:Store Batch Result and Timeline;

stop
@enduml
```

---

## 5. Candidate Freshness / Periodic Update Flow

This flow explains the periodic update concept. If a candidate appears again after some time with new skills, projects, certifications, or experience, HireX updates the existing profile instead of creating duplicate records.

```plantuml
@startuml
title HireX Candidate Freshness and Refresh Flow

start

:Candidate Data Found Again\nfrom Source / Excel / Portal;
:Identify Candidate\nusing Email / Phone / LinkedIn / Resume Metadata;

if (Candidate Exists in Database?) then (Yes)
  :Compare Old Profile with New Source Data;
  if (Changes Found?) then (Yes)
    :Update Candidate Profile;
    :Store Refresh Change Record;
    :Add Candidate Timeline Event;
    :Mark Profile as Fresh;
  else (No)
    :Update Last Seen Date;
  endif
else (No)
  :Create New Candidate Profile;
  :Store Source Record;
endif

:Candidate Becomes Available\nfor Future Validator Runs;

stop
@enduml
```

---

## 6. HR Review Flow for Middle Threshold Candidates

In HireX, HR action is required only for candidates in the middle review band. Candidates above the pass threshold are automatically shortlisted for R1, and candidates below the review threshold are automatically rejected for that role.

```plantuml
@startuml
title HireX HR Review Flow

start

:Validator Result Generated;

if (Decision?) then (PASS)
  :Auto Shortlist for R1;
  :No HR Action Required;
elseif (REVIEW)
  :Show Candidate to HR;
  :Show Score Breakdown,\nMissing Skills, Reasons, Resume Evidence;
  if (HR Decision?) then (Move Forward)
    :Move Candidate to R1 Shortlist;
  elseif (Hold)
    :Move Candidate to Held Tab;
  else (Reject)
    :Move Candidate to Rejected Tab;
    :Store HR Rejection Reason;
    :Keep Candidate in Reusable Pool;
  endif
else (FAIL)
  :Auto Reject for Current Role;
  :Store Validator Rejection Reasons;
  :Keep Candidate in Reusable Pool;
endif

stop
@enduml
```

---

## 7. Data Storage and Audit Flow

This diagram shows how the main data is stored. The goal is to keep one master candidate record and connect it to multiple jobs, batches, validator results, and HR decisions.

```plantuml
@startuml
title HireX Data Storage and Audit Model

entity "Candidate Profile" as Candidate
entity "Candidate Identity" as Identity
entity "Resume / Parsed Resume" as Resume
entity "Job Requirement" as Job
entity "Application" as Application
entity "Validator Result" as Validator
entity "Intake Batch" as Batch
entity "Sourcing Batch" as Sourcing
entity "HR Review Action" as HR
entity "Candidate Timeline" as Timeline
entity "Refresh Change" as Refresh

Candidate ||--o{ Identity : has
Candidate ||--o{ Resume : has
Candidate ||--o{ Application : applies_to
Job ||--o{ Application : receives
Application ||--o{ Validator : evaluated_by
Batch ||--o{ Validator : contains
Sourcing ||--o{ Refresh : tracks
Candidate ||--o{ Refresh : updates
Candidate ||--o{ Timeline : records
Application ||--o{ HR : reviewed_by
Validator ||--o{ HR : evidence_for

@enduml
```

---

## 8. What Is Implemented vs Future

### Implemented Now

- Candidate pool intake from Excel/source files.
- Job requirement selection and active/draft/inactive handling.
- Candidate deduplication and identity matching.
- Pre-screen validator with PASS, REVIEW, FAIL outcomes.
- Batch-based execution and dashboard filtering.
- PostgreSQL storage for candidate, job, application, resume, parsed resume, validator result, batch, HR decision, and timeline data.
- Reusable talent pool for rejected/available candidates.
- Profile freshness and refresh change tracking.
- Reason bank and structured rejection reasons.
- Validator versioning and scoring metadata.
- HR operations dashboard for candidate evidence and decisions.

### Planned Next

- Real sourcing integrations from LinkedIn, Naukri, Indeed, Internshala, and company portals.
- R1 screening and behavioral agent.
- R1 dashboard with transcript, strengths, weaknesses, and go/no-go signal.
- T1 technical and adaptive agent.
- T1 dashboard with technical score, skill coverage, and question analysis.
- T2 advanced technical and adaptive agent.
- D1 passive integrity monitor for tab switch, copy-paste, face presence, multiple people, mic/audio, and screen/window anomalies.
- M1 master intelligence engine for capacity prediction, T2 necessity prediction, hiring forecast, knowledge graph, and interview question ROI.
- HR co-pilot for candidate summary, red flags, recommendation, and final questions.
- Candidate, recruiter, HR, and admin dashboards for full workflow coverage.

---

## 9. Summary

The current implemented HireX workflow covers candidate intake, validation, batch tracking, reusable pool storage, HR review, and audit-ready scoring. The planned full architecture extends this foundation into AI-based interviews, technical assessment, behavioral screening, integrity monitoring, intelligence dashboards, and HR co-pilot support. This phased approach allows the team to start with a strong validator and data foundation, then add R1, T1, T2, HR gates, D1, M1, and co-pilot features without changing the core candidate database design.
