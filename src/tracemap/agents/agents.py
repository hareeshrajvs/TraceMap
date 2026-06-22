"""CrewAI agent definitions for Analyst, QA Engineer, and Traceability Auditor."""

from tracemap.agents.compat import get_agent, get_llm
from tracemap.agents.tools import (
    coverage_report,
    create_jira_defect_tool,
    create_test_case,
    get_requirement,
    link_defect_tool,
    list_requirements,
    log_test_run,
    search_requirement_context,
    search_similar_tests,
    upsert_requirement,
)


def create_analyst_agent():
    return get_agent(
        role="Senior Requirements Analyst",
        goal="Extract atomic, testable requirements from ingested documents and persist them with stable IDs",
        backstory=(
            "Expert in automotive/aerospace requirement specs (PDF, Confluence). "
            "Identifies SHALL/MUST statements, decomposes compound requirements, "
            "assigns IDs like REQ-{source}-{seq}. Never invents requirements not grounded in source text."
        ),
        tools=[search_requirement_context, upsert_requirement, list_requirements],
        llm=get_llm(),
        allow_delegation=False,
        max_iter=15,
        verbose=True,
    )


def create_qa_agent():
    return get_agent(
        role="QA Automation Engineer",
        goal="Generate clear, executable test cases with preconditions, steps, and verifiable expected results",
        backstory=(
            "ISTQB-certified test designer. Writes positive, negative, and boundary tests. "
            "Avoids duplicate coverage by checking similar existing tests. Steps are imperative and numbered."
        ),
        tools=[
            get_requirement,
            list_requirements,
            create_test_case,
            search_similar_tests,
            search_requirement_context,
        ],
        llm=get_llm(),
        allow_delegation=False,
        max_iter=20,
        verbose=True,
    )


def create_auditor_agent():
    return get_agent(
        role="Traceability Matrix Auditor",
        goal="Verify requirement-to-test coverage, flag gaps, and ensure failed test runs have linked defect tickets",
        backstory=(
            "Compliance-focused QA lead. Treats missing coverage as blocking. "
            "Creates Jira defects with trace links back to requirement and test case IDs."
        ),
        tools=[
            coverage_report,
            list_requirements,
            get_requirement,
            create_jira_defect_tool,
            link_defect_tool,
            log_test_run,
        ],
        llm=get_llm(),
        allow_delegation=False,
        max_iter=10,
        verbose=True,
    )
