from __future__ import annotations

import streamlit as st

from tracemap.ui.theme import status_badge_html


def render_defect_badge(jira_key: str | None, jira_url: str = "") -> None:
    if not jira_key:
        st.markdown("—")
        return
    if jira_key.startswith("MOCK-"):
        st.markdown(f"`{jira_key}` *(mock)*")
    elif jira_url:
        link = f"{jira_url.rstrip('/')}/browse/{jira_key}"
        st.markdown(f"[{jira_key}]({link})")
    else:
        st.markdown(f"`{jira_key}`")
