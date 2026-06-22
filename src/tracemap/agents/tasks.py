"""CrewAI task definitions for the traceability pipeline."""

from __future__ import annotations

from tracemap.agents.agents import create_analyst_agent, create_auditor_agent, create_qa_agent
from tracemap.agents.compat import get_task
from tracemap.agents.schemas import AuditReport, RequirementBatch, TestCaseBatch


def build_parse_requirements_task(ingest_context: dict):
    analyst = create_analyst_agent()
    candidates_json = ingest_context.get("candidates_json", "[]")
    description = f"""
Analyze the ingested document for source_ref={ingest_context.get('source_ref')}
(type={ingest_context.get('source_type')}).

Pre-extracted candidates:
{candidates_json}

Instructions:
1. Use search_requirement_context to verify each candidate against source text.
2. Split compound requirements into atomic items.
3. Assign stable IDs: REQ-{{source_prefix}}-{{3-digit-seq}}.
4. Persist each via upsert_requirement (pass requirement_json as a JSON string).
5. Return RequirementBatch JSON only — no prose.
"""
    return get_task(
        description=description,
        expected_output="JSON matching RequirementBatch schema with persisted requirements",
        agent=analyst,
        output_json=RequirementBatch,
    )


def build_generate_test_cases_task(parse_task):
    qa = create_qa_agent()
    description = """
Generate test cases for all requirements from the prior task.

Instructions:
1. For each requirement_id, call get_requirement.
2. Produce 1-3 test cases: at least one positive, consider negative/boundary.
3. Check search_similar_tests before creating to avoid duplicates.
4. Persist via create_test_case with sequence numbers starting at 1.
5. Return a JSON list of TestCaseBatch objects only.
"""
    return get_task(
        description=description,
        expected_output="JSON list of TestCaseBatch with created test case details",
        agent=qa,
        context=[parse_task],
        output_json=TestCaseBatch,
    )


def build_audit_task(parse_task, qa_task):
    auditor = create_auditor_agent()
    description = """
Audit traceability for the current ingestion batch.

Instructions:
1. Call coverage_report.
2. List every uncovered requirement in recommendations.
3. For each failed run without a defect, call create_jira_defect then link_defect.
4. Return AuditReport JSON with coverage_pct, gaps, defects_created, recommendations.
"""
    return get_task(
        description=description,
        expected_output="JSON matching AuditReport schema",
        agent=auditor,
        context=[parse_task, qa_task],
        output_json=AuditReport,
    )


def build_qa_only_task(requirement_id: str):
    qa = create_qa_agent()
    description = f"""
Generate test cases for requirement_id={requirement_id} only.

Instructions:
1. Call get_requirement for {requirement_id}.
2. Produce 1-3 test cases and persist via create_test_case.
3. Return TestCaseBatch JSON for this requirement.
"""
    return get_task(
        description=description,
        expected_output=f"TestCaseBatch JSON for {requirement_id}",
        agent=qa,
        output_json=TestCaseBatch,
    )


def build_audit_only_task():
    auditor = create_auditor_agent()
    description = """
Run traceability audit on current database state.

Instructions:
1. Call coverage_report.
2. For failed runs without defects, create_jira_defect and link_defect.
3. Return AuditReport JSON.
"""
    return get_task(
        description=description,
        expected_output="AuditReport JSON",
        agent=auditor,
        output_json=AuditReport,
    )
