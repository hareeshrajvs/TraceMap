from __future__ import annotations

import json

from tracemap.agents.compat import tool

from tracemap.agents.schemas import RequirementDraft, TestCaseDraft
from tracemap.db import repository
from tracemap.integrations.jira_client import create_defect
from tracemap.vector.chroma_store import index_document, search_context

_ingest_context: dict = {}


def set_ingest_context(
    source_type: str,
    source_ref: str,
    doc_hash: str,
    raw_text: str,
    candidates_json: str,
) -> None:
    _ingest_context.update(
        {
            "source_type": source_type,
            "source_ref": source_ref,
            "doc_hash": doc_hash,
            "raw_text": raw_text,
            "candidates_json": candidates_json,
        }
    )


@tool("index_document_chunks")
def index_document_chunks(raw_text: str, doc_hash: str, source_ref: str, source_type: str) -> str:
    """Index document text chunks into ChromaDB for semantic search."""
    count = index_document(raw_text, doc_hash, source_ref, source_type)
    return json.dumps({"chunks_indexed": count})


@tool("get_document_hash")
def get_document_hash(source_ref: str) -> str:
    """Return stored SHA-256 hash for a source reference, or null."""
    stored = repository.get_stored_doc_hash(source_ref)
    return json.dumps({"doc_hash": stored})


@tool("search_requirement_context")
def search_requirement_context(query: str, top_k: int = 5) -> str:
    """Search indexed requirement document chunks by semantic similarity."""
    source_ref = _ingest_context.get("source_ref")
    results = search_context(query, top_k=top_k, source_ref=source_ref)
    return json.dumps(results)


@tool("upsert_requirement")
def upsert_requirement(requirement_json: str) -> str:
    """Persist a requirement from JSON matching RequirementDraft schema."""
    data = json.loads(requirement_json)
    draft = RequirementDraft.model_validate(data)
    ctx = _ingest_context
    req_id = repository.upsert_requirement(
        req_id=draft.id,
        title=draft.title,
        description=draft.description,
        source_type=ctx.get("source_type", "PDF"),
        source_ref=ctx.get("source_ref", ""),
        doc_hash=ctx.get("doc_hash", ""),
        metadata_json=json.dumps({"acceptance_criteria": draft.acceptance_criteria}),
    )
    return json.dumps({"requirement_id": req_id})


@tool("get_requirement")
def get_requirement(requirement_id: str) -> str:
    """Fetch a requirement by ID."""
    row = repository.get_requirement(requirement_id)
    if not row:
        return json.dumps({"error": f"Requirement {requirement_id} not found"})
    return json.dumps(row)


@tool("list_requirements")
def list_requirements(source_ref: str = "") -> str:
    """List requirement summaries, optionally filtered by source_ref."""
    ref = source_ref if source_ref else None
    rows = repository.list_requirements(ref)
    return json.dumps([r.__dict__ for r in rows])


@tool("create_test_case")
def create_test_case(requirement_id: str, test_case_json: str, sequence: int = 1) -> str:
    """Create a test case for a requirement from TestCaseDraft JSON."""
    data = json.loads(test_case_json)
    draft = TestCaseDraft.model_validate(data)
    tc_id = f"TC-{requirement_id}-{sequence:02d}"
    repository.create_test_case(
        test_case_id=tc_id,
        requirement_id=requirement_id,
        title=draft.title,
        steps=draft.steps,
        expected_result=draft.expected_result,
        pre_conditions=draft.pre_conditions,
        test_type=draft.test_type,
    )
    return json.dumps({"test_case_id": tc_id})


@tool("search_similar_tests")
def search_similar_tests(query: str, top_k: int = 3) -> str:
    """Find similar existing test cases by title or expected result."""
    results = repository.search_test_cases(query, limit=top_k)
    return json.dumps(results)


@tool("log_test_run")
def log_test_run(test_case_id: str, status: str, execution_logs: str = "") -> str:
    """Log a test execution result."""
    run_id = repository.log_test_run(test_case_id, status, execution_logs or None)
    return json.dumps({"test_run_id": run_id})


@tool("coverage_report")
def coverage_report() -> str:
    """Return traceability coverage metrics and gap lists."""
    report = repository.get_coverage_report()
    return json.dumps(
        {
            "coverage_pct": report.coverage_pct,
            "uncovered_ids": report.uncovered_ids,
            "failed_without_defect": report.failed_without_defect,
        }
    )


@tool("create_jira_defect")
def create_jira_defect_tool(test_run_id: int, summary: str, description: str) -> str:
    """Create a Jira defect for a failed test run."""
    key = create_defect(summary, description, test_run_id=test_run_id)
    return json.dumps({"jira_key": key})


@tool("link_defect")
def link_defect_tool(test_run_id: int, jira_key: str, severity: str = "Major") -> str:
    """Link a Jira defect key to a test run."""
    repository.link_defect(test_run_id, jira_key, severity=severity)
    return json.dumps({"linked": True, "jira_key": jira_key})
