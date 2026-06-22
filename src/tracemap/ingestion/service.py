from __future__ import annotations

import hashlib
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from tracemap.ingestion.base import IngestResult, RequirementCandidate
from tracemap.ingestion.confluence_extractor import extract_from_confluence
from tracemap.ingestion.doors_extractor import extract_from_doors
from tracemap.ingestion.pdf_extractor import extract_from_pdf

Input1Type = Literal["pdf", "confluence"]
Input2Type = Literal["pdf", "doors"]


@dataclass
class DualIngestInput:
    input1_type: Input1Type
    input2_type: Input2Type
    input1_pdf: object | None = None
    input1_confluence_url: str = ""
    input2_pdf: object | None = None
    input2_doors_link: str = ""
    input2_doors_file: object | None = None


def merge_ingest_results(results: list[IngestResult]) -> IngestResult:
    """Combine multiple ingest results into one, deduplicating requirement IDs."""
    if not results:
        raise ValueError("At least one ingest result is required")
    if len(results) == 1:
        return results[0]

    raw_parts = [f"--- {r.source_type}: {r.source_ref} ---\n{r.raw_text}" for r in results]
    raw_text = "\n\n".join(raw_parts)
    source_ref = " | ".join(f"{r.source_type}:{r.source_ref}" for r in results)
    source_types = {r.source_type for r in results}
    source_type = results[0].source_type if len(source_types) == 1 else "PDF"

    seen_ids: set[str] = set()
    candidates: list[RequirementCandidate] = []
    for result in results:
        for cand in result.requirement_candidates:
            if cand.id in seen_ids:
                continue
            seen_ids.add(cand.id)
            candidates.append(cand)

    combined_hash = hashlib.sha256(
        "|".join(r.doc_hash for r in results).encode("utf-8")
    ).hexdigest()

    return IngestResult(
        source_type=source_type,
        source_ref=source_ref,
        doc_hash=combined_hash,
        raw_text=raw_text,
        requirement_candidates=candidates,
    )


def _save_uploaded_pdf(uploaded) -> str:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(uploaded.read())
        return tmp.name


def extract_input1(input_type: Input1Type, pdf_upload, confluence_url: str) -> IngestResult:
    if input_type == "pdf":
        if pdf_upload is None:
            raise ValueError("Input 1: Please upload a PDF file.")
        return extract_from_pdf(_save_uploaded_pdf(pdf_upload))
    if not confluence_url or not confluence_url.strip():
        raise ValueError("Input 1: Please enter a Confluence page URL.")
    return extract_from_confluence(confluence_url.strip())


def extract_input2(
    input_type: Input2Type,
    pdf_upload,
    doors_link: str,
    doors_file,
) -> IngestResult:
    if input_type == "pdf":
        if pdf_upload is None:
            raise ValueError("Input 2: Please upload a PDF file.")
        return extract_from_pdf(_save_uploaded_pdf(pdf_upload))

    export_bytes = None
    export_filename = None
    if doors_file is not None:
        export_bytes = doors_file.read()
        export_filename = doors_file.name

    if not doors_link.strip() and not export_bytes:
        raise ValueError("Input 2: Provide a DOORS link or upload a DOORS export (CSV/XML).")

    return extract_from_doors(
        doors_link=doors_link.strip(),
        export_bytes=export_bytes,
        export_filename=export_filename,
    )


def extract_dual_inputs(
    input1_type: Input1Type,
    input1_pdf,
    input1_confluence_url: str,
    input2_type: Input2Type,
    input2_pdf,
    input2_doors_link: str,
    input2_doors_file,
) -> IngestResult:
    """Extract from both inputs and merge into a single IngestResult."""
    r1 = extract_input1(input1_type, input1_pdf, input1_confluence_url)
    r2 = extract_input2(input2_type, input2_pdf, input2_doors_link, input2_doors_file)
    return merge_ingest_results([r1, r2])


def extract_from_sources(
    *,
    pdf_path: str | Path | None = None,
    confluence_url: str | None = None,
) -> IngestResult:
    """Legacy helper: extract from PDF path and/or Confluence URL."""
    results: list[IngestResult] = []
    if pdf_path:
        results.append(extract_from_pdf(pdf_path))
    if confluence_url and confluence_url.strip():
        results.append(extract_from_confluence(confluence_url.strip()))
    if not results:
        raise ValueError("Provide a PDF file and/or a Confluence URL.")
    return merge_ingest_results(results)
