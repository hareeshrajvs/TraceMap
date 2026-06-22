# TraceMap Code Flow

## Module Dependency Graph

```
ui/app.py
  ├── ui/pages/* ──► db/repository.py
  │                └── agents/process.py
  ├── agents/process.py
  │     ├── ingestion/base.py
  │     ├── agents/tools.py ──► db/repository.py
  │     │                     ├── vector/chroma_store.py
  │     │                     └── integrations/jira_client.py
  │     ├── agents/tasks.py ──► agents/agents.py
  │     └── agents/compat.py (optional crewai)
  └── config.py
```

## Ingestion Code Path

```
pdf_extractor.extract_from_pdf(path)
  └── base.compute_doc_hash(raw_text)
  └── base.extract_requirement_candidates(raw_text)
  └── returns IngestResult

confluence_extractor.extract_from_confluence(url)
  └── atlassian Confluence API + BeautifulSoup
  └── same base pipeline as PDF
```

## Pipeline Code Path (`run_pipeline`)

```python
# Entry: agents/process.py :: run_pipeline(ingest_result)

1. init_db()
2. get_stored_doc_hash(source_ref) → skip if unchanged
3. ingest_only() → index_document() + store_doc_hash()
4. set_ingest_context() for tool access
5. check_ollama_health()

   if use_llm and ollama online:
       crew.kickoff()  # Analyst → QA → Auditor tasks
   else:
       _persist_candidates_deterministic()
       _run_audit_deterministic()

6. finish_pipeline_run() → PipelineResult
```

## Tool → Repository Mapping

| Tool (`agents/tools.py`) | Repository function |
|--------------------------|-------------------|
| `upsert_requirement` | `repository.upsert_requirement()` |
| `get_requirement` | `repository.get_requirement()` |
| `list_requirements` | `repository.list_requirements()` |
| `create_test_case` | `repository.create_test_case()` |
| `search_similar_tests` | `repository.search_test_cases()` |
| `log_test_run` | `repository.log_test_run()` |
| `coverage_report` | `repository.get_coverage_report()` |
| `link_defect` | `repository.link_defect()` |
| `search_requirement_context` | `chroma_store.search_context()` |
| `index_document_chunks` | `chroma_store.index_document()` |
| `create_jira_defect` | `jira_client.create_defect()` |

## UI Event Flow

### Ingest Page

```
User uploads PDF → extract_from_pdf → session_state.last_ingest_result
User clicks "Index Only" → ingest_only(result)
User clicks "Generate All" → run_pipeline(result, on_progress=callback)
  └── pipeline_status updated → pipeline_status component renders stepper
```

### Matrix Page

```
repository.get_matrix_rows() → grouped by requirement_id
  └── st.expander per requirement
        └── test case rows with status badges + defect links
Export buttons → pandas DataFrame → st.download_button
```

### Execute Page

```
list_requirements() → select test case
Save Run → repository.log_test_run()
Save + Audit → log_test_run() + run_re_audit()
  └── failed runs → jira_client.create_defect() → repository.link_defect()
```

## Key Data Models

```python
# ingestion/base.py
@dataclass IngestResult:
    source_type, source_ref, doc_hash, raw_text, requirement_candidates

# agents/schemas.py (Pydantic — CrewAI task outputs)
RequirementDraft, RequirementBatch
TestCaseDraft, TestCaseBatch
AuditReport

# agents/process.py
@dataclass PipelineResult:
    status, ingest_result, requirements, test_cases, audit_report, error
```

## Entry Points

| Command | Module |
|---------|--------|
| `tracemap-init-db` | `tracemap.scripts.init_db:main` |
| `tracemap-ui` | `tracemap.scripts.run_ui:main` |
| `streamlit run src/tracemap/ui/app.py` | Direct UI launch |
