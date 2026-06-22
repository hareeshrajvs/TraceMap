---
name: tracemap-ui
description: Build and modify the TraceMap Streamlit dashboard. Use when implementing pages, components, theme, matrix table, pipeline stepper, or Plotly charts.
---

# TraceMap UI

## Pages

Dashboard, Ingest, Matrix, Execute, Settings — routed from `ui/app.py`.

## Structure

- `ui/pages/` — page render functions
- `ui/components/` — reusable widgets
- `ui/theme.py` — colors and status badges
- `ui/state.py` — session state keys

## Rules

- Status badges via `theme.status_badge_html()` / `STATUS_COLORS`
- Matrix: expandable rows, CSV/JSON export
- Pipeline runs synchronously with `st.spinner` + progress callback
- Plotly charts use `theme.COLORS`

## Run

```bash
tracemap-ui
```
