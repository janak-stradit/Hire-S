# HireX Talent Taxonomy Inheritance Report

Date: 2026-06-21

## Sources Reviewed

- `Resumes/skill_taxonomy.json`
- `Resumes/roles_strategy.json`
- `Resumes/skill_profiles.json`
- `Resumes/skills_seed.sql`
- `Resumes/schema.sql`
- `Resumes/companies.json`

## Inherited Into HireX

- 1,681 canonical skills after merging the JSON taxonomy and nonduplicate SQL seed skills.
- 311 skill aliases for normalization.
- 1,043 role strategies.
- 48 reusable skill profiles.
- Role families, categories, primary keywords, secondary keywords, seniority patterns,
  certification preferences, project tags, ATS weights, and parser profile metadata.

The source contained 47 explicit skill profiles. Forty-one cloud roles referenced a missing
`cloud_devops_core` profile. HireX repaired this by composing the existing `cloud_core` and
`devops_core` profiles, producing 48 validated runtime profiles without dropping roles.

## Runtime Integration

- Compiled artifact: `hirex/data/talent_taxonomy.json`.
- Compiler: `scripts/build_talent_taxonomy.py`.
- Runtime registry: `hirex/taxonomy/registry.py`.
- Resume parsing now uses canonical skills and aliases from the compiled taxonomy.
- Longest non-overlapping matching avoids double-counting `Apache Kafka` as both `Apache Kafka`
  and `Kafka`.
- Required JD skills remain controlled by HR and are not expanded automatically.
- Role strategy keywords enrich preferred skills in the JD workbook, where they influence keyword
  relevance without becoming mandatory gates.
- Existing education and certification matching remains separately normalized.

## Intentionally Not Inherited

`schema.sql` was not executed because it belongs to another application and defines conflicting
users, sessions, billing, email, organization, and resume-asset tables. HireX retained its own
SQLAlchemy/Alembic schema.

`companies.json` contains 6,464 company records. It was reviewed but not included in runtime or
database behavior because company matching is not currently required. This avoids adding unused
data and keeps the future company-normalization boundary explicit.

## Rebuild Procedure

When any source taxonomy changes:

1. Run `python scripts/build_talent_taxonomy.py`.
2. Run `python -c "from pathlib import Path; from hirex.excel_intake.workbooks import create_requirement_template; create_requirement_template(Path('storage/job_requirements/jd_input.xlsx'))"`.
3. Run `pytest`.

The compiled artifact records SHA-256 hashes for all inherited source files so changes remain auditable.
