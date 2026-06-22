# TraceMap

End-to-end requirement traceability platform connecting **PDF**, **Confluence**, and (future) **DOORS** requirements to structured test cases, with local LLM agents, SQLite storage, ChromaDB semantic search, and a Streamlit dashboard.

## Clone the repository

**HTTPS**

```bash
git clone https://github.com/hareeshrajvs/TraceMap.git
cd TraceMap
```

**SSH**

```bash
git clone git@github.com:hareeshrajvs/TraceMap.git
cd TraceMap
```

## Setup (first time)

### 1. Prerequisites

| Requirement | Version | Required? |
|-------------|---------|-----------|
| Python | **3.10 or newer** | Yes |
| Git | Any recent version | Yes |
| Ollama | Latest | Optional (deterministic fallback when offline) |

Check your Python version:

```bash
python3 --version   # must be 3.10+
```

### 2. Create a virtual environment

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

**Windows (Command Prompt)**

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

Your shell prompt should show `(.venv)` when the environment is active.

### 3. Install dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"
```

If editable install fails, use the requirements file instead:

```bash
pip install -r requirements.txt
pip install pytest ruff
export PYTHONPATH=src   # Windows: set PYTHONPATH=src
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` only if you need Confluence, Jira, or a custom Ollama model. Local development works out of the box with defaults.

### 5. Initialize the database

```bash
tracemap-init-db
```

This creates `data/tracemap.db` and required directories.

### 6. Verify the installation

```bash
python scripts/verify.py
```

Expected output ends with `=== VERIFY_OK ===`.

Optional unit tests:

```bash
pytest
```

## Run the app

### Start the dashboard

Make sure your virtual environment is activated, then:

```bash
tracemap-ui
```

**Alternative (direct Streamlit command):**

```bash
streamlit run src/tracemap/ui/app.py
```

Open the app in your browser:

**http://localhost:8501**

### First-time usage in the UI

1. **Ingest** — Upload a PDF or paste a Confluence URL, click **Extract / Preview**
2. **Generate All** — Runs the traceability pipeline (requirements + test cases + audit)
3. **Matrix** — Review the Requirement → Test Case → Run → Defect grid
4. **Execute** — Log test results (PASSED / FAILED / BLOCKED)
5. **Settings** — Check Ollama, SQLite, ChromaDB, and Jira connectivity

### Optional: enable LLM pipeline (Ollama)

Without Ollama, **Generate All** uses deterministic mode (still creates requirements and basic test cases).

```bash
# Install Ollama from https://ollama.com, then:
ollama pull qwen2.5-coder:14b
ollama serve
```

Confirm Ollama is running:

```bash
curl http://localhost:11434/api/tags
```

## CLI commands reference

| Command | Description |
|---------|-------------|
| `tracemap-ui` | Launch Streamlit dashboard |
| `tracemap-init-db` | Create / reset SQLite schema |
| `python scripts/verify.py` | End-to-end health check (no Ollama needed) |
| `python scripts/smoke_ingest.py --pdf spec.pdf` | Test PDF extraction |
| `python scripts/smoke_ingest.py --confluence-url "URL"` | Test Confluence extraction |
| `pytest` | Run unit tests |

## Documentation

| Document | Description |
|----------|-------------|
| [docs/SETUP.md](docs/SETUP.md) | Detailed setup, env vars, troubleshooting |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Four-layer system design and database schema |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | User flows and pipeline modes |
| [docs/CODE_FLOW.md](docs/CODE_FLOW.md) | Module dependencies and code paths |

## Architecture overview

```
PDF / Confluence → Ingestion → ChromaDB + SQLite
                              ↓
                    CrewAI (Analyst → QA → Auditor)
                              ↓
                    Traceability Matrix + Jira Defects
                              ↓
                      Streamlit Dashboard
```

## Project structure

```
TraceMap/
├── src/tracemap/          # Application source
│   ├── ingestion/         # PDF + Confluence extractors
│   ├── db/                # SQLAlchemy models + repository
│   ├── vector/            # ChromaDB semantic index
│   ├── agents/            # CrewAI agents, tasks, pipeline
│   ├── integrations/      # Jira client
│   └── ui/                # Streamlit dashboard (5 pages)
├── docs/                  # Architecture, workflow, setup
├── scripts/               # init_db, verify, smoke_ingest
├── .env.example           # Environment template
└── data/                  # Created at runtime (gitignored)
```

## Troubleshooting (quick)

| Problem | Fix |
|---------|-----|
| `command not found: tracemap-ui` | Activate `.venv` and run `pip install -e ".[dev]"` |
| `No module named 'crewai'` | Use Python 3.10+ |
| Port 8501 in use | `streamlit run src/tracemap/ui/app.py --server.port 8502` |
| Ollama offline | App still works in deterministic mode |
| Confluence / Jira errors | Optional; leave credentials blank for local-only use |

Full troubleshooting: [docs/SETUP.md](docs/SETUP.md)

## License

MIT
