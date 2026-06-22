import streamlit as st

from tracemap.ui.components.header import render_header
from tracemap.ui.components.matrix_table import render_matrix_table


def render() -> None:
    render_header("Traceability Matrix", subtitle="Requirement → Test Case → Run → Defect")
    filters = st.session_state.get("matrix_filters", {})
    c1, c2, c3, c4 = st.columns(4)
    filters["source"] = c1.selectbox(
        "Source",
        ["All", "PDF", "CONFLUENCE", "DOORS"],
        index=["All", "PDF", "CONFLUENCE", "DOORS"].index(filters.get("source", "All"))
        if filters.get("source", "All") in ["All", "PDF", "CONFLUENCE", "DOORS"]
        else 0,
    )
    filters["coverage"] = c2.selectbox(
        "Coverage",
        ["All", "Uncovered only"],
        index=["All", "Uncovered only"].index(filters.get("coverage", "All"))
        if filters.get("coverage", "All") in ["All", "Uncovered only"]
        else 0,
    )
    filters["status"] = c3.selectbox(
        "Status",
        ["All", "PASSED", "FAILED", "BLOCKED", "UNCOVERED", "NOT_RUN"],
        index=0,
    )
    filters["search"] = c4.text_input("Search", value=filters.get("search", ""))
    st.session_state.matrix_filters = filters
    render_matrix_table(filters)
