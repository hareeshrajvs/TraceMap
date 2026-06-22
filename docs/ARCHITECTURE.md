# TraceMap Architecture

TraceMap is a **local-first**, four-layer platform for end-to-end requirement traceability: from document ingestion through AI-assisted test case generation to defect tracking.

## System Topology

```
┌────────────────────────────────────────────────────────────────────────┐
│                     1. DATA INGESTION LAYER                            │
│  [Confluence API] ──► [BeautifulSoup4] ──┐                             │
│  [Requirement PDFs] ──► [pdfplumber]     ──┼──► IngestResult           │
└──────────────────────────────────────────┼─────────────────────────────┘
                                           ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     2. AGENTIC ORCHESTRATION LAYER                     │
│              CrewAI: Analyst → QA Engineer → Auditor                   │
│              (Ollama LLM or deterministic fallback)                    │
└──────────────────────────────────────────┼─────────────────────────────┘
                                           ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     3. DATA & RETRIEVAL LAYER                          │
│  ChromaDB (semantic index)     SQLite (traceability matrix)            │
└──────────────────────────────────────────┼─────────────────────────────┘
                                           ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     4. PRESENTATION & INTEGRATION LAYER                │
│  Streamlit Dashboard              Jira REST API (optional)             │
└────────────────────────────────────────────────────────────────────────┘
```

## Layer Details

### Layer 1 — Data Ingestion

| Module | Responsibility |
|--------|----------------|
| `ingestion/base.py` | `IngestResult`, `doc_hash`, candidate heuristics |
| `ingestion/pdf_extractor.py` | PDF text + table extraction via pdfplumber |
| `ingestion/confluence_extractor.py` | Confluence page fetch + HTML cleanup |

All extractors produce a unified `IngestResult`. Re-ingest is gated by SHA-256 `doc_hash`.

### Layer 2 — Agentic Orchestration

| Module | Responsibility |
|--------|----------------|
| `agents/agents.py` | CrewAI agent definitions |
| `agents/tasks.py` | Task prompts and output schemas |
| `agents/tools.py` | Tool functions (DB, Chroma, Jira) |
| `agents/process.py` | Pipeline orchestration + sub-processes |
| `agents/compat.py` | Optional CrewAI import (graceful degradation) |

**Agents:**

1. **Requirements Analyst** — parse and persist atomic requirements
2. **QA Automation Engineer** — generate test cases per requirement
3. **Traceability Auditor** — coverage gaps + Jira defect sync

### Layer 3 — Data & Retrieval

| Store | Path | Purpose |
|-------|------|---------|
| SQLite | `data/tracemap.db` | Requirements, test cases, runs, defects |
| ChromaDB | `data/chroma/` | Semantic document chunks (bge-large-en-v1.5) |

**Entity chain:** `Requirement → TestCase → TestRun → Defect`

### Layer 4 — Presentation & Integration

| Module | Responsibility |
|--------|----------------|
| `ui/app.py` | Streamlit shell + sidebar navigation |
| `ui/pages/*` | Dashboard, Ingest, Matrix, Execute, Settings |
| `integrations/jira_client.py` | Jira bug creation (mock fallback) |

## Database Schema

```
requirements (id PK, title, description, source_type, source_ref, doc_hash, metadata_json)
    └── test_cases (id PK, requirement_id FK CASCADE)
            └── test_runs (id PK autoincrement, test_case_id FK CASCADE)
                    └── defects (jira_key PK, test_run_id FK CASCADE)

pipeline_runs (id, source_ref, status, started_at, finished_at, counts)
document_hashes (source_ref PK, doc_hash)
```

`source_type` values: `PDF`, `CONFLUENCE`, `DOORS` (schema-ready, ingestion deferred).

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| SQLite + local Chroma | Zero external infrastructure; portable dev setup |
| Deterministic fallback | Pipeline works without Ollama/CrewAI for CI and offline dev |
| Lazy CrewAI import | Core tests and ingestion run on Python 3.9 without crewai |
| doc_hash gate | Avoid redundant indexing and LLM runs on unchanged documents |
| Mock Jira keys | `MOCK-BUG-*` when credentials absent |

## Future: DOORS Integration

Reserve `source_type=DOORS` and `metadata_json` on requirements. Add `doors_extractor.py` implementing the same `IngestResult` contract — no agent or UI changes required.
