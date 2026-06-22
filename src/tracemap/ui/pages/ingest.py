import streamlit as st

from tracemap.agents.process import ingest_only, run_pipeline
from tracemap.ingestion.confluence_extractor import extract_from_confluence
from tracemap.ingestion.pdf_extractor import extract_from_pdf
from tracemap.ui.components.header import render_header
from tracemap.ui.components.ingest_panel import render_action_buttons, render_preview
from tracemap.ui.components.pipeline_status import render_pipeline_status
from tracemap.ui.state import set_pipeline_status


def render() -> None:
    render_header("Ingest Documents", subtitle="Import requirements from PDF or Confluence")

    left, right = st.columns(2)
    with left:
        st.subheader("Source Input")
        tab_pdf, tab_conf = st.tabs(["PDF", "Confluence"])
        uploaded = None
        conf_url = ""
        with tab_pdf:
            uploaded = st.file_uploader("Drop PDF here", type=["pdf"], key="pdf_upload")
        with tab_conf:
            conf_url = st.text_input("Confluence URL", key="conf_url")

        if st.button("Extract / Preview", type="secondary"):
            try:
                if uploaded:
                    import tempfile

                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                        tmp.write(uploaded.read())
                        tmp_path = tmp.name
                    result = extract_from_pdf(tmp_path)
                    st.session_state.last_ingest_result = result
                elif conf_url:
                    result = extract_from_confluence(conf_url)
                    st.session_state.last_ingest_result = result
                else:
                    st.warning("Provide a PDF file or Confluence URL.")
            except Exception as exc:
                st.error(str(exc))

    result = st.session_state.get("last_ingest_result")
    with right:
        st.subheader("Preview")
        render_preview(result)

    index_only, generate_all = render_action_buttons(result)

    if index_only and result:
        ingest_only(result)
        st.success("Document indexed.")
        st.rerun()

    if generate_all and result:
        set_pipeline_status("ingest", 5, "Starting pipeline…")

        def on_progress(phase: str, pct: int, message: str) -> None:
            set_pipeline_status(phase, pct, message)

        with st.spinner("Running traceability pipeline…"):
            pipeline_result = run_pipeline(result, on_progress=on_progress)

        st.session_state.pipeline_status["running"] = False
        if pipeline_result.status == "completed":
            st.success(
                f"Pipeline complete: {len(pipeline_result.requirements)} requirements, "
                f"{len(pipeline_result.test_cases)} test cases."
            )
        elif pipeline_result.status == "skipped":
            st.info("Document unchanged — pipeline skipped.")
        else:
            st.error(pipeline_result.error or "Pipeline failed")

    render_pipeline_status(st.session_state.get("pipeline_status", {}))
