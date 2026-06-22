import streamlit as st

from tracemap.ui.theme import coverage_color, status_badge_html


def render_metric_cards(stats: dict) -> None:
    cols = st.columns(4)
    metrics = [
        ("Requirements", stats.get("requirements", 0), ""),
        ("Test Cases", stats.get("test_cases", 0), ""),
        ("Coverage", f"{stats.get('coverage_pct', 0)}%", "coverage"),
        ("Open Defects", stats.get("open_defects", 0), ""),
    ]
    for col, (label, value, kind) in zip(cols, metrics):
        with col:
            st.metric(label, value)
            if kind == "coverage":
                color = coverage_color(float(stats.get("coverage_pct", 0)))
                st.markdown(
                    f"<span style='color:{color};font-size:0.85em;'>Target ≥ 80%</span>",
                    unsafe_allow_html=True,
                )


def render_gap_alerts(stats: dict) -> None:
    st.subheader("Gap Alerts")
    uncovered = stats.get("uncovered_count", 0)
    failed_gap = stats.get("failed_without_defect", 0)
    if uncovered == 0 and failed_gap == 0:
        st.success("No coverage gaps detected.")
        return
    if uncovered:
        c1, c2 = st.columns([3, 1])
        c1.warning(f"{uncovered} requirements without test coverage")
        if c2.button("View in Matrix", key="dash_matrix"):
            st.session_state.nav_page = "Matrix"
            st.session_state.matrix_filters["coverage"] = "Uncovered only"
            st.rerun()
    if failed_gap:
        c1, c2 = st.columns([3, 1])
        c1.warning(f"{failed_gap} failed runs missing Jira defects")
        if c2.button("Re-Audit", key="dash_reaudit"):
            from tracemap.agents.process import run_re_audit

            run_re_audit()
            st.success("Re-audit complete")
            st.rerun()
