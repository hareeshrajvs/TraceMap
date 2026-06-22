# TraceMap Setup Guide

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | **3.10+** (recommended) | CrewAI requires 3.10+; core ingestion works on 3.9 |
| Ollama | Latest | Optional; deterministic mode when offline |
| LLM model | `qwen2.5-coder:14b` | `ollama pull qwen2.5-coder:14b` |
| Git | Any | Clone from `git@github.com:hareeshrajvs/TraceMap.git` |

## Installation

```bash
git clone git@github.com:hareeshrajvs/TraceMap.git
cd TraceMap

python3.10 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"

cp .env.example .env
# Edit .env with your credentials (optional for local dev)

tracemap-init-db
```

## Environment Variables

Copy `.env.example` to `.env`:

```bash
# Ollama (local LLM)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen2.5-coder:14b

# Storage (relative to project root)
DATABASE_URL=sqlite:///data/tracemap.db
CHROMA_PATH=data/chroma
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5

# Confluence (optional)
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_USER=your-email@example.com
CONFLUENCE_API_TOKEN=

# Jira (optional — mock defects when unset)
JIRA_URL=https://your-domain.atlassian.net
JIRA_USER=your-email@example.com
JIRA_API_TOKEN=
JIRA_PROJECT_KEY=PROJ
```

### Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OLLAMA_BASE_URL` | No | `http://localhost:11434/v1` | OpenAI-compatible Ollama endpoint |
| `OLLAMA_MODEL` | No | `qwen2.5-coder:14b` | Model for CrewAI agents |
| `DATABASE_URL` | No | `sqlite:///data/tracemap.db` | SQLite connection string |
| `CHROMA_PATH` | No | `data/chroma` | ChromaDB persist directory |
| `EMBEDDING_MODEL` | No | `BAAI/bge-large-en-v1.5` | Sentence-transformers model |
| `CONFLUENCE_*` | No | — | Required only for Confluence ingestion |
| `JIRA_*` | No | — | Required only for live Jira defects |

## Running TraceMap

### Dashboard

```bash
tracemap-ui
# equivalent: streamlit run src/tracemap/ui/app.py
```

Open http://localhost:8501

### CLI Tools

```bash
# Initialize database
tracemap-init-db

# Smoke test ingestion
python scripts/smoke_ingest.py --pdf path/to/spec.pdf
python scripts/smoke_ingest.py --confluence-url "https://…/wiki/…"

# Verify end-to-end (deterministic mode)
python scripts/verify.py
```

### Ollama

```bash
ollama serve                  # if not running as service
ollama pull qwen2.5-coder:14b
curl http://localhost:11434/api/tags   # health check
```

## Data Directories

Created automatically (gitignored):

```
data/
├── tracemap.db      # SQLite database
├── chroma/          # ChromaDB vectors
└── uploads/         # (future) uploaded PDF cache
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `No module named 'crewai'` | Use Python 3.10+ and `pip install -e ".[dev]"` |
| Ollama status `offline` | Start Ollama; pipeline uses deterministic fallback |
| Ollama status `no_model` | Run `ollama pull qwen2.5-coder:14b` |
| Confluence auth failed | Verify `CONFLUENCE_URL`, user email, API token |
| Jira shows `mock` | Expected without credentials; defects get `MOCK-BUG-*` keys |
| ChromaDB slow first run | Embedding model downloads on first index (~1.3 GB) |

## Development

```bash
pytest                          # unit tests
ruff check src tests            # lint
PYTHONPATH=src python scripts/verify.py
```
