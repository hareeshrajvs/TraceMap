from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from tracemap.agents.process import run_regenerate_tests
from tracemap.db import repository
from tracemap.ui.components.defect_badge import render_defect_badge
from tracemap.ui.theme import status_badge_html
from tracemap.vector.chroma_store import search_context


def _group_matrix_rows(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        rid = row["requirement_id"]
        grouped.setdefault(rid, []).append(row)
    return grouped


def render_matrix_table(filters: dict | None = None) -> None:
    filters = filters or {}
    rows = repository.get_matrix_rows()
    if filters.get("source", "All") != "All":
        rows = [r for r in rows if r["source_type"] == filters["source"]]
    if filters.get("coverage") == "Uncovered only":
        rows = [r for r in rows if r["last_status"] == "UNCOVERED"]
    if filters.get("status", "All") != "All":
        rows = [r for r in rows if r["last_status"] == filters["status"]]
    search = filters.get("search", "").strip().lower()
    if search:
        rows = [
            r
            for r in rows
            if search in r["requirement_id"].lower()
            or search in (r["requirement_title"] or "").lower()
            or search in (r.get("test_case_id") or "").lower()
        ]

    grouped = _group_matrix_rows(rows)
    if not grouped:
        st.info("No requirements match the current filters.")
        return

    flat = pd.DataFrame(rows)
    c1, c2 = st.columns(2)
    c1.download_button(
        "Export CSV",
        flat.to_csv(index=False),
        file_name="traceability_matrix.csv",
        mime="text/csv",
    )
    c2.download_button(
        "Export JSON",
        json.dumps(rows, indent=2),
        file_name="traceability_matrix.json",
        mime="application/json",
    )

    for req_id, req_rows in grouped.items():
        header = req_rows[0]
        status = header["last_status"]
        test_count = sum(1 for r in req_rows if r.get("test_case_id"))
        badge = status_badge_html(status)
        with st.expander(
            f"{req_id} | {header['requirement_title'][:50]} | {header['source_type']} | {test_count} tests",
            expanded=req_id == st.session_state.get("selected_requirement_id"),
        ):
            for row in req_rows:
                if not row.get("test_case_id"):
                    st.markdown(f"{badge} — no test cases")
                    continue
                cols = st.columns([2, 1, 1, 1])
                cols[0].write(row["test_case_title"])
                cols[1].markdown(status_badge_html(row["last_status"]), unsafe_allow_html=True)
                with cols[2]:
                    render_defect_badge(row.get("defect_key"))
                if cols[3].button("Select", key=f"sel_{row['test_case_id']}"):
                    st.session_state.selected_test_case_id = row["test_case_id"]
                    st.session_state.selected_requirement_id = req_id

            if st.button("Show Detail", key=f"detail_{req_id}"):
                st.session_state.selected_requirement_id = req_id
                _render_detail_panel(header)


def _render_detail_panel(header: dict) -> None:
    st.markdown(f"**Requirement:** {header['requirement_id']}")
    st.write(header.get("description", ""))
    c1, c2 = st.columns(2)
    if c1.button("Regenerate Tests", key=f"regen_{header['requirement_id']}"):
        run_regenerate_tests(header["requirement_id"])
        st.success("Tests regenerated")
        st.rerun()
    if c2.button("View Source Chunk", key=f"chunk_{header['requirement_id']}"):
        chunks = search_context(header["requirement_title"], top_k=1)
        if chunks:
            st.text_area("Source chunk", chunks[0]["text"], height=150)
        else:
            st.info("No indexed chunks found.")
