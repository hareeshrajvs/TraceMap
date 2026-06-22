from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class RequirementDraft(BaseModel):
    id: str
    title: str
    description: str
    acceptance_criteria: list[str] = Field(default_factory=list)


class RequirementBatch(BaseModel):
    requirements: list[RequirementDraft]


class TestCaseDraft(BaseModel):
    title: str
    pre_conditions: Optional[str] = None
    steps: list[str] = Field(min_length=1)
    expected_result: str
    test_type: Literal["positive", "negative", "boundary"] = "positive"


class TestCaseBatch(BaseModel):
    requirement_id: str
    test_cases: list[TestCaseDraft]


class AuditReport(BaseModel):
    coverage_pct: float
    uncovered_requirement_ids: list[str]
    failed_runs_without_defects: list[int]
    defects_created: list[str]
    recommendations: list[str]
