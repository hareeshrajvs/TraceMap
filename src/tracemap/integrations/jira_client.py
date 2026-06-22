from __future__ import annotations

import uuid

from tracemap.config import get_settings


def create_defect(
    summary: str,
    description: str,
    test_run_id: int | None = None,
) -> str:
    settings = get_settings()
    if not settings.jira_configured:
        return f"MOCK-BUG-{uuid.uuid4().hex[:8].upper()}"

    try:
        from jira import JIRA

        jira = JIRA(
            server=settings.jira_url,
            basic_auth=(settings.jira_user, settings.jira_api_token),
        )
        issue_dict = {
            "project": {"key": settings.jira_project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Bug"},
        }
        if test_run_id is not None:
            issue_dict["description"] = f"{description}\n\nTest Run ID: {test_run_id}"
        issue = jira.create_issue(fields=issue_dict)
        return str(issue.key)
    except Exception:
        return f"MOCK-BUG-{uuid.uuid4().hex[:8].upper()}"


def check_jira_health() -> dict:
    settings = get_settings()
    if not settings.jira_configured:
        return {"status": "mock", "detail": "Using mock defects (no token)"}
    try:
        from jira import JIRA

        jira = JIRA(
            server=settings.jira_url,
            basic_auth=(settings.jira_user, settings.jira_api_token),
        )
        jira.myself()
        return {"status": "online", "detail": f"Project {settings.jira_project_key}"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)[:100]}
