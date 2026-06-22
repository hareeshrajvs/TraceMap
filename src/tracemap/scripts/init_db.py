"""Initialize TraceMap database."""

from tracemap.db.models import init_db


def main() -> None:
    init_db()
    print("TraceMap database initialized.")
