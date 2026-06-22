import streamlit as st

from tracemap.agents.process import check_ollama_health
from tracemap.db import repository
from tracemap.db.models import init_db
from tracemap.ui import pages
from tracemap.ui.state import init_state
from tracemap.ui.theme import COLORS, coverage_color

st.set_page_config(
    page_title="TraceMap",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_state()
init_db()

PAGES = {
    "Dashboard": pages.dashboard.render,
    "Ingest": pages.ingest.render,
    "Matrix": pages.matrix.render,
    "Execute": pages.execute.render,
    "Settings": pages.settings.render,
}

with st.sidebar:
    st.markdown("## TraceMap")
    st.caption("End-to-End Requirement Traceability")
    st.divider()
    selection = st.radio(
        "Navigation",
        list(PAGES.keys()),
        index=list(PAGES.keys()).index(st.session_state.get("nav_page", "Dashboard")),
        label_visibility="collapsed",
    )
    st.session_state.nav_page = selection
    st.divider()
    ollama = check_ollama_health()
    dot = COLORS["success"] if ollama.get("status") == "online" else COLORS["danger"]
    st.markdown(
        f"<span style='color:{dot}'>●</span> Ollama: {ollama.get('status', 'unknown')}",
        unsafe_allow_html=True,
    )
    stats = repository.get_dashboard_stats()
    pct = stats.get("coverage_pct", 0)
    color = coverage_color(pct)
    st.markdown(f"Coverage: <span style='color:{color};font-weight:600;'>{pct}%</span>", unsafe_allow_html=True)

PAGES[selection]()
