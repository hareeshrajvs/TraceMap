import streamlit as st

from tracemap.agents.process import run_pipeline
from tracemap.ui.components.header import render_header
from tracemap.ui.components.ingest_panel import (
    render_dual_source_form,
    render_preview,
    run_dual_extraction,
)
from tracemap.ui.components.pipeline_status import render_pipeline_status
from tracemap.ui.state import set_pipeline_status


def render() -> None:
    render_header(
        "Ingest Documents",
        subtitle="Input 1: PDF or Confluence · Input 2: PDF or DOORS link",
    )

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Sources")
        (
            input1_type,
            input1_pdf,
            input1_conf,
            input2_type,
            input2_pdf,
            input2_doors_link,
            input2_doors_file,
            start_processing,
        ) = render_dual_source_form()

        if start_processing:
            try:
                set_pipeline_status("ingest", 5, "Extracting from both inputs…")

                def on_progress(phase: str, pct: int, message: str) -> None:
                    set_pipeline_status(phase, pct, message)

                with st.spinner("Processing both inputs…"):
                    result = run_dual_extraction(
                        input1_type,
                        input1_pdf,
                        input1_conf,
                        input2_type,
                        input2_pdf,
                        input2_doors_link,
                        input2_doors_file,
                    )
                    st.session_state.last_ingest_result = result
                    pipeline_result = run_pipeline(result, on_progress=on_progress)

                st.session_state.pipeline_status["running"] = False
                if pipeline_result.status == "completed":
                    st.success(
                        f"Processing complete: {len(pipeline_result.requirements)} requirements, "
                        f"{len(pipeline_result.test_cases)} test cases."
                    )
                elif pipeline_result.status == "skipped":
                    st.info("Documents unchanged — processing skipped.")
                else:
                    st.error(pipeline_result.error or "Processing failed")
            except Exception as exc:
                st.session_state.pipeline_status["running"] = False
                st.error(str(exc))

    with right:
        st.subheader("Results")
        render_preview(st.session_state.get("last_ingest_result"))
        render_pipeline_status(st.session_state.get("pipeline_status", {}))
