import streamlit as st

from tracemap.agents.process import run_re_audit
from tracemap.db import repository
from tracemap.ui.components.header import render_header


def render() -> None:
    render_header("Test Execution", subtitle="Log test results and trigger defect sync")

    reqs = repository.list_requirements()
    req_options = [r.id for r in reqs]
    if not req_options:
        st.info("No requirements in database. Ingest documents first.")
        return

    left, right = st.columns(2)
    with left:
        st.subheader("Select Test Case")
        req_id = st.selectbox(
            "Requirement",
            req_options,
            index=req_options.index(st.session_state.selected_requirement_id)
            if st.session_state.selected_requirement_id in req_options
            else 0,
        )
        st.session_state.selected_requirement_id = req_id
        from tracemap.db.models import TestCase, get_db_session

        with get_db_session() as session:
            test_cases = session.query(TestCase).filter(TestCase.requirement_id == req_id).all()
        if not test_cases:
            st.warning("No test cases for this requirement.")
            return
        tc_labels = [f"{tc.id} — {tc.title[:40]}" for tc in test_cases]
        tc_ids = [tc.id for tc in test_cases]
        default_idx = (
            tc_ids.index(st.session_state.selected_test_case_id)
            if st.session_state.selected_test_case_id in tc_ids
            else 0
        )
        selected_label = st.radio("Test cases", tc_labels, index=default_idx)
        tc_id = tc_ids[tc_labels.index(selected_label)]
        st.session_state.selected_test_case_id = tc_id

    tc = repository.get_test_case(tc_id)
    with right:
        st.subheader("Log Result")
        if tc:
            st.write(f"**{tc['id']}** — {tc['title']}")
        status = st.radio("Status", ["PASSED", "FAILED", "BLOCKED"], horizontal=True)
        logs = st.text_area("Execution logs", height=120)
        c1, c2 = st.columns(2)
        save = c1.button("Save Run")
        save_audit = c2.button("Save + Audit", type="primary")

    if save or save_audit:
        run_id = repository.log_test_run(tc_id, status, logs or None)
        st.success(f"Test run {run_id} logged as {status}.")
        if save_audit:
            audit = run_re_audit()
            if status == "FAILED" and audit.defects_created:
                st.toast(f"Defect {audit.defects_created[-1]} created")
            else:
                st.toast("Re-audit complete")
        st.rerun()

    st.subheader("Run History")
    history = repository.get_test_run_history(tc_id)
    if history:
        st.dataframe(history, use_container_width=True, hide_index=True)
    else:
        st.caption("No runs recorded yet.")
