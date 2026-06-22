import pytest
from pydantic import ValidationError

from tracemap.agents.schemas import (
    RequirementBatch,
    TestCaseBatch as TCBatch,
    TestCaseDraft as TCDraft,
)


def test_requirement_batch():
    batch = RequirementBatch(
        requirements=[
            {
                "id": "REQ-PDF-001",
                "title": "Auth",
                "description": "System shall authenticate users",
            }
        ]
    )
    assert len(batch.requirements) == 1


def test_test_case_draft_requires_steps():
    tc = TCDraft(
        title="Login test",
        steps=["Step 1"],
        expected_result="Success",
    )
    assert tc.test_type == "positive"

    with pytest.raises(ValidationError):
        TCDraft(title="Bad", steps=[], expected_result="x")


def test_test_case_batch():
    batch = TCBatch(
        requirement_id="REQ-001",
        test_cases=[
            TCDraft(
                title="Positive login",
                steps=["Login"],
                expected_result="OK",
            )
        ],
    )
    assert batch.requirement_id == "REQ-001"
