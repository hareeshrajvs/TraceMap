# TraceMap Setup & Run Guide

Complete instructions to clone, configure, and run TraceMap on your machine.

---

## Table of contents

1. [Prerequisites](#prerequisites)
2. [Clone the repository](#clone-the-repository)
3. [Project setup](#project-setup)
4. [Environment configuration](#environment-configuration)
5. [Run the application](#run-the-application)
6. [Verify everything works](#verify-everything-works)
7. [Optional: Ollama LLM setup](#optional-ollama-llm-setup)
8. [Optional: Confluence & Jira](#optional-confluence--jira)
9. [Data directories](#data-directories)
10. [Troubleshooting](#troubleshooting)
11. [Development commands](#development-commands)

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python** | 3.10+ | Required. Check with `python3 --version` |
| **Git** | Any | To clone the repository |
| **pip** | Latest | Upgrade during install |
| **Ollama** | Latest | Optional — LLM pipeline; app works without it |
| **Disk space** | ~2 GB free | For Python packages + embedding model download |

TraceMap runs **locally** with no external database server. SQLite and ChromaDB files are stored under `data/`.

---

## Clone the repository

Choose HTTPS or SSH:

```bash
# HTTPS (no SSH key required)
git clone https://github.com/hareeshrajvs/TraceMap.git
cd TraceMap
```

```bash
# SSH
git clone git@github.com:hareeshrajvs/TraceMap.git
cd TraceMap
```

---

## Project setup

Run these steps from the project root (`TraceMap/`).

### Step 1 — Virtual environment

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

You must activate the virtual environment **every time** you open a new terminal before running TraceMap commands.

### Step 2 — Install packages

```bash
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"
```

This installs TraceMap in editable mode and registers CLI entry points:

- `tracemap-ui` — launch the dashboard
- `tracemap-init-db` — initialize the database

**Fallback** (if editable install fails):

```bash
pip install -r requirements.txt
pip install pytest ruff
```

When using the fallback, prefix commands with `PYTHONPATH=src` (see [Run the application](#run-the-application)).

### Step 3 — Environment file

```bash
cp .env.example .env
```

Defaults in `.env.example` are sufficient for local development. Edit `.env` only when connecting Confluence, Jira, or a custom Ollama model.

### Step 4 — Initialize database

```bash
tracemap-init-db
```

Output: `TraceMap database initialized.`

Creates:

- `data/tracemap.db` — SQLite traceability database
- `data/chroma/` — ChromaDB vector store (populated on first ingest)

---

## Environment configuration

All settings are loaded from `.env` in the project root via `pydantic-settings`.

### `.env` template

```bash
# Ollama (local LLM — optional)
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

### Variable reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OLLAMA_BASE_URL` | No | `http://localhost:11434/v1` | Ollama OpenAI-compatible API |
| `OLLAMA_MODEL` | No | `qwen2.5-coder:14b` | Model name for CrewAI agents |
| `DATABASE_URL` | No | `sqlite:///data/tracemap.db` | SQLite connection string |
| `CHROMA_PATH` | No | `data/chroma` | ChromaDB persist directory |
| `EMBEDDING_MODEL` | No | `BAAI/bge-large-en-v1.5` | Sentence-transformers model for vectors |
| `CONFLUENCE_URL` | No | — | Confluence base URL |
| `CONFLUENCE_USER` | No | — | Atlassian account email |
| `CONFLUENCE_API_TOKEN` | No | — | [API token](https://id.atlassian.com/manage-profile/security/api-tokens) |
| `JIRA_URL` | No | — | Jira instance URL |
| `JIRA_USER` | No | — | Atlassian account email |
| `JIRA_API_TOKEN` | No | — | Jira API token |
| `JIRA_PROJECT_KEY` | No | `PROJ` | Project key for defect tickets |

> **Security:** Never commit `.env`. It is listed in `.gitignore`.

---

## Run the application

### Dashboard (recommended)

```bash
# Activate venv first
source .venv/bin/activate   # macOS/Linux

tracemap-ui
```

Browser URL: **http://localhost:8501**

### Alternative launch methods

```bash
# Direct Streamlit
streamlit run src/tracemap/ui/app.py

# Custom port (if 8501 is busy)
streamlit run src/tracemap/ui/app.py --server.port 8502

# Without editable install (PYTHONPATH fallback)
PYTHONPATH=src streamlit run src/tracemap/ui/app.py
```

### Using the dashboard

| Page | What to do |
|------|------------|
| **Dashboard** | View coverage KPIs, gap alerts, recent pipeline runs |
| **Ingest** | Upload PDF or enter Confluence URL → **Extract / Preview** → **Generate All** |
| **Matrix** | Browse Requirement → Test Case → Run → Defect chain; export CSV/JSON |
| **Execute** | Select a test case, log PASSED/FAILED/BLOCKED, optionally **Save + Audit** |
| **Settings** | Check Ollama, SQLite, ChromaDB, Confluence, and Jira status |

### Pipeline buttons (Ingest page)

| Button | Behavior |
|--------|----------|
| **Index Only** | Extract text and index in ChromaDB — no LLM |
| **Generate All** | Full pipeline: requirements → test cases → audit |

When Ollama is unavailable, **Generate All** automatically uses **deterministic mode** (still creates requirements and basic test cases).

---

## Verify everything works

Run these after setup, before using the UI:

```bash
# 1. Unit tests
pytest

# 2. End-to-end pipeline (uses temp DB, no Ollama required)
python scripts/verify.py
```

Expected verify output:

```
=== TraceMap Verification ===
1. Ingestion: N requirement candidates
2. Pipeline: status=completed, reqs=N, tcs=N
3. Coverage: 100.0%
...
=== VERIFY_OK ===
```

### Smoke-test document ingestion

```bash
# PDF
python scripts/smoke_ingest.py --pdf path/to/your/spec.pdf

# Confluence (requires .env credentials)
python scripts/smoke_ingest.py --confluence-url "https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title"
```

---

## Optional: Ollama LLM setup

For AI-generated test cases via CrewAI agents:

1. Install [Ollama](https://ollama.com)
2. Pull the model:

```bash
ollama pull qwen2.5-coder:14b
```

3. Start the server (if not running as a background service):

```bash
ollama serve
```

4. Verify:

```bash
curl http://localhost:11434/api/tags
```

5. Confirm in the app: **Settings** page → Ollama status should show `online`.

---

## Optional: Confluence & Jira

### Confluence

1. Create an API token at https://id.atlassian.com/manage-profile/security/api-tokens
2. Set in `.env`:

```bash
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_USER=you@example.com
CONFLUENCE_API_TOKEN=your-token
```

3. On the **Ingest** page, paste a Confluence page URL and click **Extract / Preview**.

### Jira

1. Set Jira variables in `.env` (same API token works for Jira Cloud).
2. When a test run is marked **FAILED** and you click **Save + Audit**, TraceMap creates a Bug ticket.
3. Without credentials, defects use mock keys: `MOCK-BUG-XXXXXXXX`.

---

## Data directories

Created automatically at runtime (gitignored):

```
data/
├── tracemap.db      # SQLite — requirements, test cases, runs, defects
└── chroma/          # Vector embeddings for semantic search
```

To reset all local data:

```bash
rm -rf data/
tracemap-init-db
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `python3: command not found` | Install Python 3.10+ from python.org or your package manager |
| `requires-python >=3.10` | Upgrade Python; CrewAI does not support 3.9 |
| `command not found: tracemap-ui` | Activate `.venv`; run `pip install -e ".[dev]"` |
| `No module named 'tracemap'` | Run from project root with venv active, or set `PYTHONPATH=src` |
| `No module named 'crewai'` | Reinstall with Python 3.10+: `pip install -e ".[dev]"` |
| Streamlit won't open | Check terminal for URL; try `--server.port 8502` |
| Ollama status `offline` | Run `ollama serve`; app still works in deterministic mode |
| Ollama status `no_model` | Run `ollama pull qwen2.5-coder:14b` |
| Confluence auth failed | Verify URL, email, and API token in `.env` |
| Jira shows `mock` | Expected without credentials |
| First ingest is slow | Embedding model (~1.3 GB) downloads on first Chroma index |
| `UNIQUE constraint failed: test_cases` | Reset DB: `rm -rf data/ && tracemap-init-db` |

---

## Development commands

```bash
# Lint
ruff check src tests

# Tests with coverage output
pytest -v

# Re-init database
tracemap-init-db

# Run UI in development
tracemap-ui
```

For architecture and workflow details, see [ARCHITECTURE.md](ARCHITECTURE.md) and [WORKFLOW.md](WORKFLOW.md).
