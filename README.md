# TraceMap

End-to-end requirement traceability platform connecting **PDF**, **Confluence**, and (future) **DOORS** requirements to structured test cases, with local LLM agents, SQLite storage, ChromaDB semantic search, and a Streamlit dashboard.

## Documentation

| Document | Description |
|----------|-------------|
| [docs/SETUP.md](docs/SETUP.md) | Installation, environment variables, troubleshooting |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Four-layer system design and database schema |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | User flows and pipeline modes |
| [docs/CODE_FLOW.md](docs/CODE_FLOW.md) | Module dependencies and code paths |

## Architecture Overview

```
PDF / Confluence → Ingestion → ChromaDB + SQLite
                              ↓
                    CrewAI (Analyst → QA → Auditor)
                              ↓
                    Traceability Matrix + Jira Defects
                              ↓
                      Streamlit Dashboard
```

## Quick Start

```bash
python3.10 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
tracemap-init-db
python scripts/verify.py          # end-to-end check (no Ollama required)
tracemap-ui                       # open http://localhost:8501
```

## Prerequisites

- **Python 3.10+** (recommended; core ingestion works on 3.9 without CrewAI)
- [Ollama](https://ollama.com/) + `qwen2.5-coder:14b` (optional — deterministic fallback when offline)

## Pipeline Modes

| Mode | Trigger | LLM |
|------|---------|-----|
| Index Only | Ingest page | No |
| Generate All | Ingest page | Yes (or deterministic fallback) |
| Re-Audit | Execute / Dashboard | No |

## Project Structure

```
src/tracemap/
├── ingestion/       # PDF + Confluence extractors
├── db/              # SQLAlchemy models + repository
├── vector/          # ChromaDB semantic index
├── agents/          # CrewAI agents, tasks, pipeline
├── skills/          # Tool groupings for agents
├── integrations/    # Jira client
└── ui/              # Streamlit dashboard (5 pages)
docs/                # Architecture, workflow, setup guides
scripts/             # init_db, smoke_ingest, verify
.cursor/skills/      # Cursor IDE project skills
```

## Verification

```bash
pytest                            # 7 unit tests
python scripts/verify.py          # full deterministic pipeline
python scripts/smoke_ingest.py --pdf spec.pdf
```

## Configuration

See [docs/SETUP.md](docs/SETUP.md) for all environment variables. Secrets go in `.env` (never committed).

## License

MIT
