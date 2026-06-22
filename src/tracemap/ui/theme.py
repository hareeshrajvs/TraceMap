"""TraceMap UI theme tokens and status helpers."""

COLORS = {
    "primary": "#2563EB",
    "primary_dark": "#1D4ED8",
    "success": "#16A34A",
    "warning": "#D97706",
    "danger": "#DC2626",
    "neutral": "#6B7280",
    "surface": "#F9FAFB",
    "border": "#E5E7EB",
}

STATUS_COLORS = {
    "PASSED": COLORS["success"],
    "FAILED": COLORS["danger"],
    "BLOCKED": COLORS["warning"],
    "UNCOVERED": COLORS["neutral"],
    "NOT_RUN": COLORS["neutral"],
}


def status_badge_html(status: str) -> str:
    color = STATUS_COLORS.get(status.upper(), COLORS["neutral"])
    return (
        f'<span style="background:{color};color:white;padding:2px 8px;'
        f'border-radius:4px;font-size:0.85em;">{status.upper()}</span>'
    )


def coverage_color(pct: float) -> str:
    if pct >= 80:
        return COLORS["success"]
    if pct >= 50:
        return COLORS["warning"]
    return COLORS["danger"]
