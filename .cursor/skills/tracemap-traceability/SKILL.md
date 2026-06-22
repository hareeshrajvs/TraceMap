---
name: tracemap-traceability
description: Manage TraceMap traceability matrix, coverage metrics, test runs, and Jira defect linking. Use when working on repository queries, Streamlit matrix UI, coverage reports, or Jira integration.
---

# TraceMap Traceability

## Chain

Requirement → TestCase → TestRun → Defect

## Coverage

`requirements_with_tests / total_requirements`

## Gap Types

- Uncovered requirement (no test cases)
- Failed run without linked defect
- Blocked test

## Jira

Env vars: `JIRA_URL`, `JIRA_USER`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY`

Mock mode: keys prefixed `MOCK-BUG-` when creds absent.

## Key Files

- `db/repository.py` — CRUD + `get_coverage_report()`, `get_matrix_rows()`
- `integrations/jira_client.py` — defect creation
