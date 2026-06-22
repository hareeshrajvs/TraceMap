from __future__ import annotations

import csv
import io
from pathlib import Path
from xml.etree import ElementTree

from tracemap.ingestion.base import (
    IngestResult,
    RequirementCandidate,
    compute_doc_hash,
    extract_requirement_candidates,
)


def _parse_doors_csv(content: str) -> list[RequirementCandidate]:
    """Parse IBM DOORS CSV export (Id, Object Heading, Object Text columns)."""
    candidates: list[RequirementCandidate] = []
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        return candidates

    fields = {f.lower().strip(): f for f in reader.fieldnames}
    id_col = fields.get("id") or fields.get("object identifier") or fields.get("identifier")
    title_col = fields.get("object heading") or fields.get("heading") or fields.get("title")
    text_col = (
        fields.get("object text")
        or fields.get("text")
        or fields.get("description")
        or fields.get("content")
    )

    for idx, row in enumerate(reader, start=1):
        req_id = (row.get(id_col) or "").strip() if id_col else ""
        title = (row.get(title_col) or "").strip() if title_col else ""
        description = (row.get(text_col) or "").strip() if text_col else ""
        if not req_id:
            req_id = f"REQ-DOORS-{idx:03d}"
        if not title and description:
            title = description.split(".")[0][:120]
        if not description:
            description = title
        if title or description:
            candidates.append(
                RequirementCandidate(
                    id=req_id.upper().replace("_", "-"),
                    title=title[:255] or req_id,
                    description=description[:1000],
                )
            )
    return candidates


def _parse_doors_xml(content: str) -> list[RequirementCandidate]:
    """Parse simple DOORS XML export with requirement elements."""
    candidates: list[RequirementCandidate] = []
    root = ElementTree.fromstring(content)
    for idx, elem in enumerate(root.iter(), start=1):
        tag = elem.tag.lower()
        if "req" not in tag and "object" not in tag and "item" not in tag:
            continue
        req_id = elem.get("id") or elem.get("identifier") or f"REQ-DOORS-{idx:03d}"
        title = elem.get("heading") or elem.get("title") or (elem.text or "").strip()[:120]
        description = (elem.text or "").strip() or title
        if title or description:
            candidates.append(
                RequirementCandidate(
                    id=req_id.upper().replace("_", "-"),
                    title=title[:255],
                    description=description[:1000],
                )
            )
    return candidates


def _read_doors_file(path: Path) -> tuple[str, list[RequirementCandidate]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return text, _parse_doors_csv(text)
    if suffix == ".xml":
        return text, _parse_doors_xml(text)
    return text, extract_requirement_candidates(text, source_prefix="DOORS")


def extract_from_doors(
    doors_link: str,
    export_bytes: bytes | None = None,
    export_filename: str | None = None,
) -> IngestResult:
    """
    Extract requirements from a DOORS module link and/or exported file.

    doors_link: DOORS module URL, module path, or identifier (stored in source_ref).
    export_bytes: Optional CSV/XML export uploaded from DOORS.
    """
    doors_link = doors_link.strip()
    if not doors_link and not export_bytes:
        raise ValueError("Provide a DOORS link or upload a DOORS export file (CSV/XML).")

    source_ref = doors_link or (export_filename or "doors-export")
    raw_text_parts: list[str] = []
    candidates: list[RequirementCandidate] = []

    if export_bytes:
        name = (export_filename or "export.csv").lower()
        content = export_bytes.decode("utf-8", errors="replace")
        raw_text_parts.append(content)
        if name.endswith(".csv"):
            candidates = _parse_doors_csv(content)
        elif name.endswith(".xml"):
            candidates = _parse_doors_xml(content)
        else:
            candidates = extract_requirement_candidates(content, source_prefix="DOORS")

    link_path = Path(doors_link) if doors_link else None
    if link_path and link_path.exists() and link_path.is_file():
        file_text, file_candidates = _read_doors_file(link_path)
        raw_text_parts.append(file_text)
        if not candidates:
            candidates = file_candidates

    if doors_link and not candidates:
        raw_text_parts.append(f"DOORS module reference: {doors_link}")
        candidates = extract_requirement_candidates(
            raw_text_parts[-1], source_prefix="DOORS"
        )

    raw_text = "\n\n".join(raw_text_parts) or doors_link
    if not candidates:
        candidates = [
            RequirementCandidate(
                id="REQ-DOORS-001",
                title=f"DOORS module: {doors_link[:80]}",
                description=f"Requirements linked from DOORS module: {doors_link}",
            )
        ]

    return IngestResult(
        source_type="DOORS",
        source_ref=source_ref,
        doc_hash=compute_doc_hash(raw_text),
        raw_text=raw_text,
        requirement_candidates=candidates,
    )
