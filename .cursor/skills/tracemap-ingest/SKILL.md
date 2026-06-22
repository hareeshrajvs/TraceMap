---
name: tracemap-ingest
description: Ingest requirements from PDF and Confluence into TraceMap. Use when implementing or debugging extractors, doc_hash logic, requirement candidate parsing, or Chroma indexing.
---

# TraceMap Ingestion

## Quick Start

1. Extractors return `IngestResult` from `src/tracemap/ingestion/base.py`
2. PDF: `pdfplumber` via `pdf_extractor.py`
3. Confluence: `atlassian-python-api` + BeautifulSoup via `confluence_extractor.py`
4. Compare `doc_hash` before re-indexing

## Smoke Test

```bash
python scripts/smoke_ingest.py --pdf path/to/spec.pdf
python scripts/smoke_ingest.py --confluence-url "https://…"
```

## Rules

- Never commit API tokens
- `source_type`: `PDF`, `CONFLUENCE`, or `DOORS` (future)
- Candidates use regex for `REQ-\d+` and SHALL/MUST heuristics
