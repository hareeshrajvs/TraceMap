#!/usr/bin/env python3
"""Smoke test for PDF and Confluence ingestion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tracemap.ingestion.confluence_extractor import extract_from_confluence
from tracemap.ingestion.pdf_extractor import extract_from_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description="TraceMap ingestion smoke test")
    parser.add_argument("--pdf", type=str, help="Path to PDF file")
    parser.add_argument("--confluence-url", type=str, help="Confluence page URL")
    args = parser.parse_args()

    if not args.pdf and not args.confluence_url:
        parser.error("Provide --pdf and/or --confluence-url")

    if args.pdf:
        result = extract_from_pdf(args.pdf)
        print(f"\n=== PDF: {args.pdf} ===")
        print(f"doc_hash: {result.doc_hash[:16]}…")
        print(f"candidates: {len(result.requirement_candidates)}")
        for c in result.requirement_candidates[:5]:
            print(f"  {c.id}: {c.title[:60]}")

    if args.confluence_url:
        result = extract_from_confluence(args.confluence_url)
        print(f"\n=== Confluence: {args.confluence_url} ===")
        print(f"doc_hash: {result.doc_hash[:16]}…")
        print(f"candidates: {len(result.requirement_candidates)}")
        print(json.dumps([c.__dict__ for c in result.requirement_candidates[:3]], indent=2))


if __name__ == "__main__":
    main()
