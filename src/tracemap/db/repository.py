from __future__ import annotations

import datetime
import json
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from tracemap.db.models import (
    Defect,
    DocumentHash,
    PipelineRun,
    Requirement,
    TestCase,
    TestRun,
    get_db_session,
)


@dataclass
class RequirementSummary:
    id: str
    title: str
    source_type: str
    source_ref: str
    test_count: int


@dataclass
class CoverageReport:
    coverage_pct: float
    total_requirements: int
    covered_requirements: int
    uncovered_ids: list[str]
    failed_without_defect: list[int]


def get_stored_doc_hash(source_ref: str) -> str | None:
    with get_db_session() as session:
        row = session.get(DocumentHash, source_ref)
        return row.doc_hash if row else None


def store_doc_hash(source_ref: str, doc_hash: str) -> None:
    with get_db_session() as session:
        row = session.get(DocumentHash, source_ref)
        if row:
            row.doc_hash = doc_hash
            row.updated_at = datetime.datetime.utcnow()
        else:
            session.add(DocumentHash(source_ref=source_ref, doc_hash=doc_hash))
        session.commit()


def upsert_requirement(
    req_id: str,
    title: str,
    description: str,
    source_type: str,
    source_ref: str,
    doc_hash: str,
    metadata_json: str | None = None,
) -> str:
    with get_db_session() as session:
        existing = session.get(Requirement, req_id)
        if existing:
            existing.title = title
            existing.description = description
            existing.source_type = source_type
            existing.source_ref = source_ref
            existing.doc_hash = doc_hash
            existing.metadata_json = metadata_json
            existing.updated_at = datetime.datetime.utcnow()
        else:
            session.add(
                Requirement(
                    id=req_id,
                    title=title,
                    description=description,
                    source_type=source_type,
                    source_ref=source_ref,
                    doc_hash=doc_hash,
                    metadata_json=metadata_json,
                )
            )
        session.commit()
        return req_id


def get_requirement(req_id: str) -> dict | None:
    with get_db_session() as session:
        req = session.get(Requirement, req_id)
        if not req:
            return None
        return {
            "id": req.id,
            "title": req.title,
            "description": req.description,
            "source_type": req.source_type,
            "source_ref": req.source_ref,
            "doc_hash": req.doc_hash,
            "metadata_json": req.metadata_json,
            "updated_at": req.updated_at.isoformat() if req.updated_at else None,
        }


def list_requirements(source_ref: str | None = None) -> list[RequirementSummary]:
    with get_db_session() as session:
        query = session.query(Requirement)
        if source_ref:
            query = query.filter(Requirement.source_ref == source_ref)
        rows = query.all()
        return [
            RequirementSummary(
                id=r.id,
                title=r.title,
                source_type=r.source_type,
                source_ref=r.source_ref,
                test_count=len(r.test_cases),
            )
            for r in rows
        ]


def create_test_case(
    test_case_id: str,
    requirement_id: str,
    title: str,
    steps: list[str],
    expected_result: str,
    pre_conditions: str | None = None,
    test_type: str = "positive",
) -> str:
    with get_db_session() as session:
        session.add(
            TestCase(
                id=test_case_id,
                requirement_id=requirement_id,
                title=title,
                pre_conditions=pre_conditions,
                steps=json.dumps(steps),
                expected_result=expected_result,
                test_type=test_type,
            )
        )
        session.commit()
        return test_case_id


def search_test_cases(query: str, limit: int = 5) -> list[dict]:
    with get_db_session() as session:
        pattern = f"%{query[:80]}%"
        rows = (
            session.query(TestCase)
            .filter(
                (TestCase.title.ilike(pattern))
                | (TestCase.expected_result.ilike(pattern))
            )
            .limit(limit)
            .all()
        )
        return [
            {
                "id": tc.id,
                "requirement_id": tc.requirement_id,
                "title": tc.title,
                "steps": json.loads(tc.steps),
                "expected_result": tc.expected_result,
            }
            for tc in rows
        ]


def log_test_run(
    test_case_id: str,
    status: str,
    execution_logs: str | None = None,
) -> int:
    with get_db_session() as session:
        run = TestRun(
            test_case_id=test_case_id,
            status=status.upper(),
            execution_logs=execution_logs,
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        return run.id


def link_defect(
    test_run_id: int,
    jira_key: str,
    severity: str | None = None,
    status: str = "Open",
) -> str:
    with get_db_session() as session:
        session.merge(
            Defect(
                jira_key=jira_key,
                test_run_id=test_run_id,
                severity=severity,
                status=status,
            )
        )
        session.commit()
        return jira_key


def get_coverage_report() -> CoverageReport:
    with get_db_session() as session:
        total = session.query(func.count(Requirement.id)).scalar() or 0
        if total == 0:
            return CoverageReport(0.0, 0, 0, [], [])

        covered_ids = {
            row[0]
            for row in session.query(TestCase.requirement_id).distinct().all()
        }
        all_ids = [row[0] for row in session.query(Requirement.id).all()]
        uncovered = [rid for rid in all_ids if rid not in covered_ids]

        failed_runs = (
            session.query(TestRun)
            .filter(TestRun.status == "FAILED")
            .options(joinedload(TestRun.defects))
            .all()
        )
        failed_without = [r.id for r in failed_runs if not r.defects]

        covered_count = len(covered_ids)
        pct = round((covered_count / total) * 100, 1)
        return CoverageReport(pct, total, covered_count, uncovered, failed_without)


def get_matrix_rows() -> list[dict]:
    with get_db_session() as session:
        requirements = (
            session.query(Requirement)
            .options(
                joinedload(Requirement.test_cases)
                .joinedload(TestCase.runs)
                .joinedload(TestRun.defects)
            )
            .all()
        )
        rows = []
        for req in requirements:
            if not req.test_cases:
                rows.append(
                    {
                        "requirement_id": req.id,
                        "requirement_title": req.title,
                        "source_type": req.source_type,
                        "description": req.description,
                        "test_case_id": None,
                        "test_case_title": None,
                        "last_status": "UNCOVERED",
                        "defect_key": None,
                    }
                )
                continue
            for tc in req.test_cases:
                last_run = max(tc.runs, key=lambda r: r.executed_at, default=None) if tc.runs else None
                defect_key = None
                if last_run and last_run.defects:
                    defect_key = last_run.defects[0].jira_key
                rows.append(
                    {
                        "requirement_id": req.id,
                        "requirement_title": req.title,
                        "source_type": req.source_type,
                        "description": req.description,
                        "test_case_id": tc.id,
                        "test_case_title": tc.title,
                        "last_status": last_run.status if last_run else "NOT_RUN",
                        "defect_key": defect_key,
                    }
                )
        return rows


def get_dashboard_stats() -> dict:
    with get_db_session() as session:
        req_count = session.query(func.count(Requirement.id)).scalar() or 0
        tc_count = session.query(func.count(TestCase.id)).scalar() or 0
        open_defects = (
            session.query(func.count(Defect.jira_key))
            .filter(Defect.status.in_(["Open", "In Progress"]))
            .scalar()
            or 0
        )
        coverage = get_coverage_report()
        run_statuses = (
            session.query(TestRun.status, func.count(TestRun.id))
            .group_by(TestRun.status)
            .all()
        )
        source_coverage = {}
        for (source_type,) in session.query(Requirement.source_type).distinct():
            sub_total = (
                session.query(func.count(Requirement.id))
                .filter(Requirement.source_type == source_type)
                .scalar()
                or 0
            )
            sub_covered = (
                session.query(func.count(Requirement.id.distinct()))
                .join(TestCase)
                .filter(Requirement.source_type == source_type)
                .scalar()
                or 0
            )
            source_coverage[source_type] = round(
                (sub_covered / sub_total * 100) if sub_total else 0, 1
            )

        recent_runs = (
            session.query(PipelineRun)
            .order_by(PipelineRun.started_at.desc())
            .limit(10)
            .all()
        )
        return {
            "requirements": req_count,
            "test_cases": tc_count,
            "coverage_pct": coverage.coverage_pct,
            "open_defects": open_defects,
            "uncovered_count": len(coverage.uncovered_ids),
            "failed_without_defect": len(coverage.failed_without_defect),
            "run_statuses": dict(run_statuses),
            "source_coverage": source_coverage,
            "recent_pipeline_runs": [
                {
                    "id": r.id,
                    "source_ref": r.source_ref,
                    "status": r.status,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "requirements_count": r.requirements_count,
                    "test_cases_count": r.test_cases_count,
                }
                for r in recent_runs
            ],
        }


def create_pipeline_run(source_ref: str) -> int:
    with get_db_session() as session:
        run = PipelineRun(source_ref=source_ref, status="running")
        session.add(run)
        session.commit()
        session.refresh(run)
        return run.id


def finish_pipeline_run(
    run_id: int,
    status: str,
    requirements_count: int = 0,
    test_cases_count: int = 0,
    error: str | None = None,
) -> None:
    with get_db_session() as session:
        run = session.get(PipelineRun, run_id)
        if run:
            run.status = status
            run.finished_at = datetime.datetime.utcnow()
            run.requirements_count = requirements_count
            run.test_cases_count = test_cases_count
            run.error = error
            session.commit()


def get_test_case(test_case_id: str) -> dict | None:
    with get_db_session() as session:
        tc = session.get(TestCase, test_case_id)
        if not tc:
            return None
        return {
            "id": tc.id,
            "requirement_id": tc.requirement_id,
            "title": tc.title,
            "pre_conditions": tc.pre_conditions,
            "steps": json.loads(tc.steps),
            "expected_result": tc.expected_result,
            "test_type": tc.test_type,
        }


def get_test_run_history(test_case_id: str) -> list[dict]:
    with get_db_session() as session:
        runs = (
            session.query(TestRun)
            .filter(TestRun.test_case_id == test_case_id)
            .options(joinedload(TestRun.defects))
            .order_by(TestRun.executed_at.desc())
            .all()
        )
        return [
            {
                "id": r.id,
                "executed_at": r.executed_at.isoformat() if r.executed_at else None,
                "status": r.status,
                "execution_logs": r.execution_logs,
                "defect_key": r.defects[0].jira_key if r.defects else None,
            }
            for r in runs
        ]
