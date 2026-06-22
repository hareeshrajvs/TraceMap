import streamlit as st


def render_header(title: str, subtitle: str = "", status_chip: str = "") -> None:
    cols = st.columns([4, 1])
    with cols[0]:
        st.title(title)
        if subtitle:
            st.caption(subtitle)
    with cols[1]:
        if status_chip:
            st.markdown(f"<div style='text-align:right;padding-top:1rem;'>{status_chip}</div>", unsafe_allow_html=True)
