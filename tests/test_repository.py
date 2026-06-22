import pytest

from tracemap.db.models import init_db
from tracemap.db import repository


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from tracemap.db import models

    models._engine = None
    models._SessionLocal = None
    init_db()
    yield


def test_upsert_and_coverage():
    repository.upsert_requirement(
        "REQ-TEST-001",
        "Login",
        "User shall login",
        "PDF",
        "/tmp/spec.pdf",
        "abc123",
    )
    req = repository.get_requirement("REQ-TEST-001")
    assert req is not None
    report = repository.get_coverage_report()
    assert "REQ-TEST-001" in report.uncovered_ids

    repository.create_test_case(
        "TC-REQ-TEST-001-01",
        "REQ-TEST-001",
        "Valid login",
        ["Enter credentials", "Click login"],
        "User is authenticated",
    )
    report2 = repository.get_coverage_report()
    assert report2.coverage_pct == 100.0
