import streamlit as st

from tracemap.ui.theme import status_badge_html


def render_pipeline_status(status: dict) -> None:
    if status.get("phase") == "idle" and not status.get("running"):
        return

    st.subheader("Pipeline Progress")
    phases = ["ingest", "analyst", "qa", "auditor", "done"]
    labels = ["Ingest & Index", "Analyst", "QA", "Auditor", "Done"]
    current = status.get("phase", "idle")
    cols = st.columns(len(labels))
    for i, (phase, label) in enumerate(zip(phases, labels)):
        with cols[i]:
            if phase == current:
                st.markdown(f"**● {label}**")
            elif phases.index(current) > i if current in phases else False:
                st.markdown(f"✓ {label}")
            else:
                st.markdown(f"○ {label}")

    pct = status.get("progress_pct", 0)
    st.progress(min(pct, 100) / 100)
    st.caption(status.get("message", ""))
    if status.get("error"):
        st.error(status["error"])
