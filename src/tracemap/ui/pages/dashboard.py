import plotly.express as px
import streamlit as st

from tracemap.db import repository
from tracemap.ui.components.header import render_header
from tracemap.ui.components.metric_cards import render_gap_alerts, render_metric_cards
from tracemap.ui.theme import COLORS


def render() -> None:
    render_header("Dashboard", subtitle="End-to-end traceability overview")
    stats = repository.get_dashboard_stats()
    render_metric_cards(stats)

    c1, c2 = st.columns(2)
    source_cov = stats.get("source_coverage", {})
    if source_cov:
        with c1:
            fig = px.bar(
                x=list(source_cov.keys()),
                y=list(source_cov.values()),
                labels={"x": "Source", "y": "Coverage %"},
                title="Coverage by Source",
                color_discrete_sequence=[COLORS["primary"]],
            )
            fig.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)
    run_statuses = stats.get("run_statuses", {})
    if run_statuses:
        with c2:
            fig = px.pie(
                names=list(run_statuses.keys()),
                values=list(run_statuses.values()),
                title="Test Run Status",
                color_discrete_sequence=[COLORS["success"], COLORS["danger"], COLORS["warning"]],
            )
            st.plotly_chart(fig, use_container_width=True)

    render_gap_alerts(stats)

    st.subheader("Recent Pipeline Runs")
    recent = stats.get("recent_pipeline_runs", [])
    if recent:
        st.dataframe(recent, use_container_width=True, hide_index=True)
    else:
        st.caption("No pipeline runs yet.")
