---
name: tracemap-dev
description: TraceMap project setup, conventions, and development workflow. Use when bootstrapping the repo, adding dependencies, running tests, or onboarding to the codebase.
---

# TraceMap Development

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
tracemap-init-db
ollama pull qwen2.5-coder:14b
```

## Layout

- `src/tracemap/` — application package
- `data/` — gitignored (SQLite, Chroma, uploads)
- No external DB services (SQLite + local Chroma only)

## Commands

```bash
pytest
ruff check src tests
tracemap-ui
python scripts/smoke_ingest.py --pdf spec.pdf
```

## Entry Points

- `tracemap-init-db` — create tables
- `tracemap-ui` — Streamlit dashboard

DOORS ingestion is schema-ready (`source_type=DOORS`) but not implemented in v1.
