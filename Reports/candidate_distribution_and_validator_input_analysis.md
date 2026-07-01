# Candidate Distribution and Validator Input Analysis

Date: 2026-06-21

## Dataset Separation

- Real resume-extracted candidates: 66.
- Synthetic candidates retained in the historical master workbook: 1,000.
- Production candidate pool: 66 real candidates.
- Production candidates with agent processing enabled: 66.

Synthetic data was analyzed for testing context but is not present in the production candidate pool
and must not determine hiring or product-quality conclusions.

## Real Candidate Domains

| Domain | Candidates |
|---|---:|
| Software Development | 33 |
| Identity and Access Management | 9 |
| Mechanical Engineering | 7 |
| SAP Finance and Controlling | 5 |
| Network Engineering | 5 |
| IT Support | 3 |
| HR | 1 |
| Testing | 1 |
| DevOps | 1 |
| Cybersecurity | 1 |

Most populated real domain: Software Development, 33 candidates.

Least populated real domains: HR, Testing, DevOps, and Cybersecurity, 1 candidate each.

## Real Candidate Roles

Most frequent exact roles:

- Software Developer: 14.
- Identity Specialist: 9.
- Software Engineer: 9.
- Full Stack Developer: 6.
- SAP CO Consultant: 5.
- Network Architect: 5.
- Mechanical Engineer: 5.
- Java Backend Developer: 3.

Roles with one candidate include DevOps Engineer, React Developer, Security Engineer, Senior Quality
Analyst, Technical Support Engineer, and Workforce Management Specialist.

## Synthetic Candidate Domains

| Domain | Candidates |
|---|---:|
| IT Support | 134 |
| Sales and Marketing | 115 |
| Software Development | 106 |
| Accounting | 104 |
| Finance | 97 |
| HR | 94 |
| Testing | 93 |
| DevOps | 88 |
| Data Engineering | 86 |
| Data Analytics | 83 |

The synthetic role column contains 399 generated role variants and is unsuitable for choosing a
production pilot role. Synthetic distributions are useful only for load and branch testing.

## Active Requirement Selection

IT Support Engineer is now active because IT Support is the most-populated synthetic domain:

- Synthetic IT Support candidates: 134.
- Real IT Support candidates: 3.

The production pool remains real-only unless the synthetic workbook is explicitly regenerated and
selected for a controlled test run.

## Current Validator Input Behavior

The existing Excel intake service filters on provenance and `agent_processing_allowed`; it does not
perform a domain/role prefilter before validation. Therefore, running the current Data Engineer batch
would send all 66 eligible real candidates to the IT Support Engineer validator when using the real pool.

Current live PostgreSQL state:

- Excel intake batches: 0.
- Applications: 0.
- Validator results: 0.
- Candidates actually sent to the validator: 0.
- Candidates eligible to be sent on the next run: 66.

## Recommended Most/Least Pilot

Use real data and run two sequential requirements because HireX intentionally allows exactly one
active requirement at a time:

1. Most-populated pilot: Software Development domain, using a generic Software Developer requirement.
2. Least-populated pilot: DevOps domain, using the existing DevOps Engineer requirement.

Expected domain-prefilter sizes are 33 and 1. This creates a useful comparison between bulk screening
and a single-candidate edge case.

Before running these pilots, add a deterministic domain/role prefilter stage so irrelevant candidates
are not scored against the active JD. The validator should receive only the selected domain/role pool,
while PostgreSQL records the excluded count and reason for audit.
