from __future__ import annotations

import streamlit as st

from tracemap.ingestion.base import IngestResult
from tracemap.ingestion.service import Input1Type, Input2Type, extract_dual_inputs


def _render_input1() -> tuple[Input1Type, object | None, str]:
    st.markdown("**Input 1** — PDF or Confluence link")
    input1_type: Input1Type = st.radio(
        "Input 1 type",
        options=["pdf", "confluence"],
        format_func=lambda x: "PDF" if x == "pdf" else "Confluence link",
        horizontal=True,
        key="input1_type",
        label_visibility="collapsed",
    )
    pdf_upload = None
    confluence_url = ""
    if input1_type == "pdf":
        pdf_upload = st.file_uploader(
            "Upload PDF (Input 1)",
            type=["pdf"],
            key="input1_pdf",
            label_visibility="collapsed",
        )
    else:
        confluence_url = st.text_input(
            "Confluence URL (Input 1)",
            key="input1_confluence",
            placeholder="https://your-domain.atlassian.net/wiki/spaces/…/pages/…",
            label_visibility="collapsed",
        )
    return input1_type, pdf_upload, confluence_url


def _render_input2() -> tuple[Input2Type, object | None, str, object | None]:
    st.markdown("**Input 2** — PDF or DOORS link")
    input2_type: Input2Type = st.radio(
        "Input 2 type",
        options=["pdf", "doors"],
        format_func=lambda x: "PDF" if x == "pdf" else "DOORS link",
        horizontal=True,
        key="input2_type",
        label_visibility="collapsed",
    )
    pdf_upload = None
    doors_link = ""
    doors_file = None
    if input2_type == "pdf":
        pdf_upload = st.file_uploader(
            "Upload PDF (Input 2)",
            type=["pdf"],
            key="input2_pdf",
            label_visibility="collapsed",
        )
    else:
        doors_link = st.text_input(
            "DOORS module link (Input 2)",
            key="input2_doors_link",
            placeholder="doors://module/path or path/to/export.csv",
            label_visibility="collapsed",
        )
        doors_file = st.file_uploader(
            "DOORS export file (optional CSV/XML)",
            type=["csv", "xml"],
            key="input2_doors_file",
            help="Upload a CSV or XML export from IBM DOORS if the link alone is not enough.",
        )
    return input2_type, pdf_upload, doors_link, doors_file


def render_dual_source_form() -> tuple[
    Input1Type, object | None, str, Input2Type, object | None, str, object | None, bool
]:
    """Render both inputs and Start Processing button. Returns inputs + button clicked."""
    input1_type, input1_pdf, input1_conf = _render_input1()
    st.divider()
    input2_type, input2_pdf, input2_doors_link, input2_doors_file = _render_input2()
    st.divider()
    start = st.button("Start Processing", type="primary", use_container_width=True)
    return (
        input1_type,
        input1_pdf,
        input1_conf,
        input2_type,
        input2_pdf,
        input2_doors_link,
        input2_doors_file,
        start,
    )


def run_dual_extraction(
    input1_type: Input1Type,
    input1_pdf,
    input1_conf: str,
    input2_type: Input2Type,
    input2_pdf,
    input2_doors_link: str,
    input2_doors_file,
) -> IngestResult:
    return extract_dual_inputs(
        input1_type=input1_type,
        input1_pdf=input1_pdf,
        input1_confluence_url=input1_conf,
        input2_type=input2_type,
        input2_pdf=input2_pdf,
        input2_doors_link=input2_doors_link,
        input2_doors_file=input2_doors_file,
    )


def render_preview(result: IngestResult | None) -> None:
    if not result:
        st.info("Fill both inputs and click **Start Processing**.")
        return

    if " | " in result.source_ref:
        st.caption("Sources")
        for part in result.source_ref.split(" | "):
            st.caption(f"· {part[:120]}")
    else:
        st.caption(f"Source: {result.source_type} — {result.source_ref[:80]}")

    st.caption(f"doc_hash: {result.doc_hash[:16]}…")
    st.write(f"**{len(result.requirement_candidates)}** requirement candidates")

    if result.requirement_candidates:
        import pandas as pd

        df = pd.DataFrame([c.__dict__ for c in result.requirement_candidates])
        st.dataframe(df[["id", "title"]], use_container_width=True, hide_index=True)
