from __future__ import annotations

import streamlit as st

from tracemap.ingestion.base import IngestResult


def render_ingest_panel() -> tuple[str, object | None, str | None]:
    """Returns (mode, file_or_none, confluence_url_or_none)."""
    tab_pdf, tab_conf = st.tabs(["PDF", "Confluence"])
    with tab_pdf:
        uploaded = st.file_uploader("Drop PDF here or click to browse", type=["pdf"])
    with tab_conf:
        conf_url = st.text_input("Confluence URL", placeholder="https://…/wiki/spaces/…/pages/…")
    mode = "pdf" if tab_pdf else "confluence"
    return mode, uploaded, conf_url


def render_preview(result: IngestResult | None) -> None:
    if not result:
        st.info("Upload a PDF or paste a Confluence URL to begin.")
        return
    st.caption(f"doc_hash: {result.doc_hash[:16]}…")
    st.write(f"**{len(result.requirement_candidates)}** candidates found")
    if result.requirement_candidates:
        import pandas as pd

        df = pd.DataFrame([c.__dict__ for c in result.requirement_candidates])
        st.dataframe(df[["id", "title"]], use_container_width=True, hide_index=True)


def render_action_buttons(result: IngestResult | None) -> tuple[bool, bool]:
    c1, c2 = st.columns(2)
    index_only = c1.button("Index Only", disabled=result is None)
    generate_all = c2.button("Generate All", type="primary", disabled=result is None)
    return index_only, generate_all
