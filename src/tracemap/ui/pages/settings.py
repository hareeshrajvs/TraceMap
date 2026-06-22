import streamlit as st

from tracemap.agents.process import check_ollama_health
from tracemap.config import get_settings
from tracemap.db import repository
from tracemap.db.models import init_db
from tracemap.integrations.jira_client import check_jira_health
from tracemap.ui.components.header import render_header
from tracemap.vector.chroma_store import get_chunk_count


def render() -> None:
    render_header("Settings", subtitle="Service health and environment")
    settings = get_settings()
    init_db()

    if st.button("Re-check All"):
        st.rerun()

    ollama = check_ollama_health()
    jira = check_jira_health()
    stats = repository.get_dashboard_stats()
    chroma_count = get_chunk_count()

    rows = [
        {
            "Service": "Ollama",
            "Status": ollama.get("status", "unknown"),
            "Detail": ollama.get("detail", ""),
        },
        {
            "Service": "SQLite",
            "Status": "ok",
            "Detail": f"{settings.db_path} ({stats.get('requirements', 0)} req)",
        },
        {
            "Service": "ChromaDB",
            "Status": "ok",
            "Detail": f"{settings.chroma_dir} ({chroma_count} chunks)",
        },
        {
            "Service": "Confluence",
            "Status": "configured" if settings.confluence_configured else "n/a",
            "Detail": settings.confluence_url or "Not configured",
        },
        {
            "Service": "Jira",
            "Status": jira.get("status", "unknown"),
            "Detail": jira.get("detail", ""),
        },
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.subheader("Environment")
    st.code(
        f"DB: {settings.database_url}\n"
        f"Chroma: {settings.chroma_path}\n"
        f"Model: {settings.ollama_model}\n"
        f"Ollama: {settings.ollama_base_url}",
        language="text",
    )
    st.caption("Copy .env.example to .env and fill in credentials.")
