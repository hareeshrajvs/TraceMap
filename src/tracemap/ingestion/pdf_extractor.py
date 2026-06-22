from __future__ import annotations

from pathlib import Path

import pdfplumber

from tracemap.ingestion.base import (
    IngestResult,
    compute_doc_hash,
    extract_requirement_candidates,
)


def extract_from_pdf(pdf_path: str | Path) -> IngestResult:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    text_parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
            for table in page.extract_tables() or []:
                for row in table:
                    if row:
                        text_parts.append(" | ".join(str(cell or "") for cell in row))

    raw_text = "\n\n".join(text_parts)
    source_ref = str(path.resolve())
    doc_hash = compute_doc_hash(raw_text)
    candidates = extract_requirement_candidates(raw_text, source_prefix="PDF")

    return IngestResult(
        source_type="PDF",
        source_ref=source_ref,
        doc_hash=doc_hash,
        raw_text=raw_text,
        requirement_candidates=candidates,
    )
