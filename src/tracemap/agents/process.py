from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable, Literal

import requests

from tracemap.agents.schemas import AuditReport, RequirementBatch, TestCaseBatch, TestCaseDraft
from tracemap.agents.tools import set_ingest_context
from tracemap.db import repository
from tracemap.db.models import init_db
from tracemap.ingestion.base import IngestResult
from tracemap.vector.chroma_store import index_document

ProgressCallback = Callable[[str, int, str], None]


@dataclass
class PipelineResult:
    status: Literal["completed", "skipped", "failed"]
    ingest_result: IngestResult
    requirements: list[str] = field(default_factory=list)
    test_cases: list[str] = field(default_factory=list)
    audit_report: AuditReport | None = None
    error: str | None = None


def check_ollama_health() -> dict:
    from tracemap.config import get_settings

    settings = get_settings()
    base = settings.ollama_base_url.replace("/v1", "")
    try:
        resp = requests.get(f"{base}/api/tags", timeout=3)
        if resp.ok:
            models = [m.get("name", "") for m in resp.json().get("models", [])]
            model_ok = any(settings.ollama_model.split(":")[0] in m for m in models)
            return {
                "status": "online" if model_ok else "no_model",
                "detail": settings.ollama_model,
                "models": models,
            }
        return {"status": "error", "detail": f"HTTP {resp.status_code}"}
    except Exception as exc:
        return {"status": "offline", "detail": str(exc)[:100]}


def ingest_only(ingest_result: IngestResult) -> IngestResult:
    """Sub-process A: extract + index without LLM."""
    init_db()
    stored = repository.get_stored_doc_hash(ingest_result.source_ref)
    if stored == ingest_result.doc_hash:
        return ingest_result
    index_document(
        ingest_result.raw_text,
        ingest_result.doc_hash,
        ingest_result.source_ref,
        ingest_result.source_type,
    )
    repository.store_doc_hash(ingest_result.source_ref, ingest_result.doc_hash)
    return ingest_result


def _persist_candidates_deterministic(ingest_result: IngestResult) -> tuple[list[str], list[str]]:
    """Fallback: persist candidates and generate basic test cases without LLM."""
    req_ids: list[str] = []
    tc_ids: list[str] = []
    for cand in ingest_result.requirement_candidates:
        repository.upsert_requirement(
            req_id=cand.id,
            title=cand.title,
            description=cand.description,
            source_type=ingest_result.source_type,
            source_ref=ingest_result.source_ref,
            doc_hash=ingest_result.doc_hash,
        )
        req_ids.append(cand.id)
        tc_id = f"TC-{cand.id}-01"
        if repository.get_test_case(tc_id) is None:
            repository.create_test_case(
                test_case_id=tc_id,
                requirement_id=cand.id,
                title=f"Verify: {cand.title[:80]}",
                steps=["Execute scenario described in requirement", "Observe system behavior"],
                expected_result="System behaves as specified in the requirement",
                pre_conditions="Test environment is available",
                test_type="positive",
            )
        tc_ids.append(tc_id)
    return req_ids, tc_ids


def _run_audit_deterministic() -> AuditReport:
    report = repository.get_coverage_report()
    defects_created: list[str] = []
    recommendations: list[str] = []
    for req_id in report.uncovered_ids:
        recommendations.append(f"Requirement {req_id} has no test coverage")
    for run_id in report.failed_without_defect:
        from tracemap.integrations.jira_client import create_defect

        key = create_defect(
            summary=f"Failed test run {run_id}",
            description=f"Automated defect for failed test run {run_id}",
            test_run_id=run_id,
        )
        repository.link_defect(run_id, key)
        defects_created.append(key)
    return AuditReport(
        coverage_pct=report.coverage_pct,
        uncovered_requirement_ids=report.uncovered_ids,
        failed_runs_without_defects=report.failed_without_defect,
        defects_created=defects_created,
        recommendations=recommendations,
    )


def run_pipeline(
    ingest_result: IngestResult,
    use_llm: bool = True,
    on_progress: ProgressCallback | None = None,
) -> PipelineResult:
    init_db()

    def progress(phase: str, pct: int, message: str) -> None:
        if on_progress:
            on_progress(phase, pct, message)

    stored = repository.get_stored_doc_hash(ingest_result.source_ref)
    if stored == ingest_result.doc_hash and not ingest_result.requirement_candidates:
        return PipelineResult(status="skipped", ingest_result=ingest_result)

    progress("ingest", 10, "Indexing document chunks…")
    ingest_only(ingest_result)

    run_id = repository.create_pipeline_run(ingest_result.source_ref)
    candidates_json = json.dumps(
        [c.__dict__ for c in ingest_result.requirement_candidates]
    )
    set_ingest_context(
        ingest_result.source_type,
        ingest_result.source_ref,
        ingest_result.doc_hash,
        ingest_result.raw_text,
        candidates_json,
    )

    ollama = check_ollama_health()
    if use_llm and ollama.get("status") != "online":
        use_llm = False
        progress("ingest", 15, f"Ollama unavailable ({ollama.get('detail')}); using deterministic mode")

    try:
        if not use_llm:
            progress("analyst", 40, "Persisting requirements (deterministic)…")
            req_ids, tc_ids = _persist_candidates_deterministic(ingest_result)
            progress("auditor", 90, "Running audit…")
            audit = _run_audit_deterministic()
            repository.finish_pipeline_run(
                run_id, "completed", len(req_ids), len(tc_ids)
            )
            progress("done", 100, "Pipeline complete")
            return PipelineResult(
                status="completed",
                ingest_result=ingest_result,
                requirements=req_ids,
                test_cases=tc_ids,
                audit_report=audit,
            )

        from tracemap.agents.agents import create_analyst_agent, create_auditor_agent, create_qa_agent
        from tracemap.agents.compat import crewai_available, get_crew, get_process_sequential
        from tracemap.agents.tasks import build_audit_task, build_generate_test_cases_task, build_parse_requirements_task

        if not crewai_available():
            raise ImportError("crewai required for LLM pipeline mode")

        ctx = {
            "source_type": ingest_result.source_type,
            "source_ref": ingest_result.source_ref,
            "candidates_json": candidates_json,
        }
        progress("analyst", 30, "Analyst parsing requirements…")
        parse_task = build_parse_requirements_task(ctx)
        qa_task = build_generate_test_cases_task(parse_task)
        audit_task = build_audit_task(parse_task, qa_task)

        crew = get_crew(
            agents=[create_analyst_agent(), create_qa_agent(), create_auditor_agent()],
            tasks=[parse_task, qa_task, audit_task],
            process=get_process_sequential(),
            verbose=True,
            memory=False,
        )
        progress("qa", 60, "QA generating test cases…")
        crew.kickoff()
        progress("auditor", 85, "Auditor checking traceability…")

        req_ids = [r.id for r in repository.list_requirements(ingest_result.source_ref)]
        tc_ids = [
            tc["id"]
            for row in repository.get_matrix_rows()
            if row["test_case_id"] and row["requirement_id"] in req_ids
            for tc in [row]
        ]
        audit = _run_audit_deterministic()
        repository.finish_pipeline_run(run_id, "completed", len(req_ids), len(tc_ids))
        progress("done", 100, "Pipeline complete")
        return PipelineResult(
            status="completed",
            ingest_result=ingest_result,
            requirements=req_ids,
            test_cases=list({t for t in tc_ids if t}),
            audit_report=audit,
        )
    except Exception as exc:
        repository.finish_pipeline_run(run_id, "failed", error=str(exc))
        progress("error", 100, str(exc))
        return PipelineResult(
            status="failed",
            ingest_result=ingest_result,
            error=str(exc),
        )


def run_re_audit(on_progress: ProgressCallback | None = None) -> AuditReport:
    if on_progress:
        on_progress("auditor", 50, "Running re-audit…")
    audit = _run_audit_deterministic()
    if on_progress:
        on_progress("done", 100, "Re-audit complete")
    return audit


def run_regenerate_tests(
    requirement_id: str,
    on_progress: ProgressCallback | None = None,
) -> list[str]:
    req = repository.get_requirement(requirement_id)
    if not req:
        return []
    if on_progress:
        on_progress("qa", 50, f"Regenerating tests for {requirement_id}…")
    tc_id = f"TC-{requirement_id}-01"
    draft = TestCaseDraft(
        title=f"Verify: {req['title'][:80]}",
        steps=["Execute requirement scenario", "Validate expected behavior"],
        expected_result="Requirement is satisfied",
        test_type="positive",
    )
    repository.create_test_case(
        test_case_id=tc_id,
        requirement_id=requirement_id,
        title=draft.title,
        steps=draft.steps,
        expected_result=draft.expected_result,
        pre_conditions=draft.pre_conditions,
        test_type=draft.test_type,
    )
    if on_progress:
        on_progress("done", 100, "Regeneration complete")
    return [tc_id]
