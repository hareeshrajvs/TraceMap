"""Launch TraceMap Streamlit UI."""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    app = Path(__file__).resolve().parents[1] / "src" / "tracemap" / "ui" / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app)], check=False)


if __name__ == "__main__":
    main()
