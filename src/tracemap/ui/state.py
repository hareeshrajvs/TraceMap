"""Streamlit session state helpers."""

import streamlit as st


def init_state() -> None:
    defaults = {
        "selected_requirement_id": None,
        "selected_test_case_id": None,
        "matrix_filters": {
            "source": "All",
            "coverage": "All",
            "status": "All",
            "search": "",
        },
        "pipeline_status": {
            "phase": "idle",
            "progress_pct": 0,
            "message": "",
            "error": None,
            "running": False,
        },
        "last_ingest_result": None,
        "nav_page": "Dashboard",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_pipeline_status(phase: str, pct: int, message: str, running: bool = True) -> None:
    st.session_state.pipeline_status = {
        "phase": phase,
        "progress_pct": pct,
        "message": message,
        "error": None,
        "running": running,
    }
