# TraceMap Workflows

## Primary User Flow: Document → Test Cases

```
Upload PDF / Confluence URL
        │
        ▼
Extract / Preview (requirement candidates)
        │
        ├── Index Only ──► Chroma index + doc_hash stored
        │
        └── Generate All ──► Full pipeline
                │
                ├── 1. Index document chunks
                ├── 2. Analyst: parse & persist requirements
                ├── 3. QA: generate test cases
                └── 4. Auditor: coverage report + defect sync
                        │
                        ▼
                Traceability Matrix (review)
```

## Pipeline Modes

| Mode | Trigger | LLM | Description |
|------|---------|-----|-------------|
| **Index Only** | Ingest page button | No | Extract text, compute hash, index Chroma |
| **Generate All** | Ingest page button | Yes* | Full Analyst → QA → Auditor crew |
| **Deterministic** | Auto when Ollama offline | No | Persist candidates + basic test cases |
| **Re-Audit** | Execute / Dashboard | No | Auditor logic: gaps + Jira for failed runs |
| **Regenerate Tests** | Matrix detail panel | No* | QA scoped to one requirement |

\* Requires Python 3.10+, CrewAI, and Ollama for LLM modes.

## Test Execution Flow

```
Execute page → Select requirement → Select test case
        │
        ├── Save Run ──► log_test_run(status, logs)
        │
        └── Save + Audit ──► log_test_run + run_re_audit()
                                    │
                                    └── FAILED? ──► create_jira_defect + link_defect
```

## Sub-Processes (process.py)

### Sub-Process A: Ingest-Only

1. Extract text (PDF or Confluence)
2. Compute `doc_hash`
3. If changed → index chunks → store hash
4. Does **not** run CrewAI

### Sub-Process B: Re-Audit Only

1. Skip Analyst + QA
2. Run coverage report
3. Create Jira defects for failed runs without linked defects

### Sub-Process C: Single-Requirement Regeneration

1. Skip Analyst (requirement exists)
2. Generate test cases for one `requirement_id`
3. Optional re-audit

## Coverage Metrics

```
coverage_pct = requirements_with_test_cases / total_requirements × 100
```

**Gap types:**

- Uncovered requirement (zero test cases)
- Failed test run without linked defect
- Blocked test (manual status from Execute page)

## Streamlit Pages

| Page | Purpose |
|------|---------|
| Dashboard | KPIs, charts, gap alerts, recent pipeline runs |
| Ingest | Upload, preview, index/generate |
| Matrix | Expandable Req → Test → Run → Defect grid |
| Execute | Log test results, run history |
| Settings | Ollama/SQLite/Chroma/Jira health checks |
