# HireX

## AI-Powered Recruitment & Interview Intelligence Platform

HireX is an AI-powered recruitment operating system designed to automate candidate screening, technical assessments, hiring intelligence, and recruiter decision support while maintaining human oversight in critical hiring decisions.

## Vision

Modern recruitment teams spend significant time reviewing resumes, conducting repetitive interviews, coordinating hiring workflows, and generating evaluation reports. HireX aims to reduce recruiter workload, improve hiring quality, and accelerate time-to-hire through intelligent automation and data-driven decision making.

## Core Components

### Candidate Portal

* Candidate registration and profile management
* Resume upload and application tracking
* Interview scheduling and status updates

### Pre-Screen Validator

* Resume and JD matching
* Experience validation
* Skill extraction and filtering
* Candidate shortlisting

### R1 Screening Agent

* Screening interview
* Behavioral assessment
* Communication evaluation
* Candidate summary generation

### T1 Technical Agent

* Technical interview
* Adaptive questioning
* Skill assessment
* Technical scoring

### D1 Integrity Monitor

* Tab switch detection
* Copy-paste monitoring
* Presence validation
* Interview integrity scoring

### H1 HR Copilot

* Candidate insights
* Strengths and weaknesses
* Hiring recommendations
* Final interview guidance

### M1 Master Intelligence Engine

* Hiring Capacity Prediction
* T2 Necessity Prediction
* Hiring Forecast Engine
* Interview Knowledge Graph
* Question ROI Engine

## Architecture

Candidate Portal
→ Pre-Screen Validator
→ R1 Screening Agent
→ R1 Dashboard
→ T1 Technical Agent
→ T1 Dashboard
→ Combined Dashboard
→ HR Review
→ HR Copilot
→ Future T2

## Technology Stack

### Backend

* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic
* Redis

### Frontend

* React
* TypeScript
* TailwindCSS

### AI Layer

* Ollama
* Groq
* Gemini
* OpenRouter

## Current Status

### Completed

* Foundation & Database Layer
* Authentication
* Candidate Profiles
* Resume Management
* Job Management
* Application Tracking
* Pre-Screen Validator Engine

### Phase 2 Validator Endpoints

* `POST /api/validator/evaluate`
* `GET /api/validator/result/{validator_result_id}`
* `GET /api/validator/application/{application_id}`
* `POST /api/validator/bulk-evaluate`
* `GET /api/validator/queues/r1`

### Excel Intake MVP

Excel is an intake adapter; PostgreSQL remains the system of record. The candidate portal can
later create the same jobs, candidates, resumes, and applications without changing the validator
or downstream agents.

1. Run `python scripts/prepare_excel_mvp_storage.py` once to prepare provenance-safe workbooks.
2. Set exactly one row in `storage/job_requirements/jd_input.xlsx` to `active`.
3. Run `python scripts/run_excel_intake.py` or call `POST /api/excel-intake/run` as HR/admin.
4. PASS candidates enter the R1 queue, REVIEW candidates enter HR review, and FAIL candidates
   are retained for audit. Shortlist and rejection workbooks are exported under `storage/`.

The production candidate pool contains only resume-extracted candidates. An optional synthetic
workbook can be regenerated for load testing with
`python scripts/prepare_excel_mvp_storage.py --include-synthetic`; it is excluded from agent
processing by default.

### Talent Taxonomy

HireX compiles the supplied Talent OS role and skill references into
`hirex/data/talent_taxonomy.json`. Rebuild it with
`python scripts/build_talent_taxonomy.py`. The validator uses canonical skills and aliases from
this artifact, while role strategies enrich preferred JD keywords without silently expanding
mandatory requirements. The foreign schema and company catalog are intentionally not applied.

### Planned

* R1 Agent
* T1 Agent
* D1 Integrity Monitor
* H1 HR Copilot
* M1 Master Intelligence Engine
* Dashboards

## Project Goal

Build a complete AI-assisted recruitment platform capable of automating the hiring lifecycle while providing recruiters with actionable insights, hiring intelligence, and human-controlled decision making.
# HR Operations Quick Start

Create the first manager account locally. The password is requested securely and is not echoed:

```powershell
python scripts/bootstrap_manager.py --email your-email@example.com --role admin
```

Start FastAPI and Next.js, sign in, then open `http://127.0.0.1:3000/operations`.

The operations flow is:

1. Select an existing job requirement or create one with **New JD**.
2. Select **Extracted real resumes** for production or **Synthetic simulation pool** for testing.
3. Review candidate count, experience range, and PASS/REVIEW thresholds.
4. Click **Run validator**, review the confirmation, then click **Confirm and run**.
5. HireX imports the selected candidates, evaluates them, stores results in PostgreSQL, and refreshes PASS/REVIEW/FAIL queues.
6. HR opens a candidate and records **Move forward**, **Hold**, or **Reject** with an audit reason.
