#!/usr/bin/env python3
"""Initialize TraceMap SQLite database."""

from tracemap.db.models import init_db


def main() -> None:
    init_db()
    print("TraceMap database initialized.")


if __name__ == "__main__":
    main()
