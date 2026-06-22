#!/usr/bin/env python3
"""End-to-end verification script for TraceMap (deterministic mode, no Ollama required)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tracemap.agents.process import check_ollama_health, run_pipeline
from tracemap.db import repository
from tracemap.db.models import init_db
from tracemap.ingestion.base import IngestResult, compute_doc_hash, extract_requirement_candidates
from tracemap.integrations.jira_client import check_jira_health
from tracemap.vector.chroma_store import get_chunk_count


def main() -> int:
    import os
    import tempfile

    db_path = tempfile.mktemp(suffix=".db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    from tracemap.db import models

    models._engine = None
    models._SessionLocal = None

    print("=== TraceMap Verification ===\n")
    init_db()

    text = """
REQ-001 User Authentication
The system shall authenticate users with valid credentials.

REQ-002 Session Timeout
The system must expire inactive sessions after 30 minutes.
"""
    candidates = extract_requirement_candidates(text, "PDF")
    result = IngestResult(
        source_type="PDF",
        source_ref="verify://sample-spec",
        doc_hash=compute_doc_hash(text),
        raw_text=text,
        requirement_candidates=candidates,
    )

    print(f"1. Ingestion: {len(candidates)} requirement candidates")
    pr = run_pipeline(result, use_llm=False)
    print(f"2. Pipeline: status={pr.status}, reqs={len(pr.requirements)}, tcs={len(pr.test_cases)}")

    if pr.status != "completed":
        print(f"   ERROR: {pr.error}")
        return 1

    coverage = pr.audit_report.coverage_pct if pr.audit_report else 0
    print(f"3. Coverage: {coverage}%")
    print(f"4. Matrix rows: {len(repository.get_matrix_rows())}")
    print(f"5. Chroma chunks: {get_chunk_count()}")
    print(f"6. Ollama: {check_ollama_health().get('status')}")
    print(f"7. Jira: {check_jira_health().get('status')}")

    run_id = repository.log_test_run(pr.test_cases[0], "FAILED", "Verification failure")
    repository.link_defect(run_id, "MOCK-BUG-VERIFY", severity="Minor")
    print(f"8. Test run + defect: run_id={run_id}")

    print("\n=== VERIFY_OK ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
