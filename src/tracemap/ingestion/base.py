from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Literal

SourceType = Literal["CONFLUENCE", "PDF", "DOORS"]

REQ_ID_PATTERN = re.compile(r"\b(REQ[-_]?\d+)\b", re.IGNORECASE)
SHALL_MUST_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:\d+[\.)]\s*)?"
    r"(?:REQ[-_]?\w+[\s:.-]*)?"
    r"(.+?\b(?:shall|must|should)\b.+)",
    re.IGNORECASE | re.DOTALL,
)
NUMBERED_SECTION = re.compile(
    r"(?:^|\n)\s*(\d+(?:\.\d+)*)\s+(.+?)(?=\n\s*\d+(?:\.\d+)*\s|\Z)",
    re.DOTALL,
)


@dataclass
class RequirementCandidate:
    id: str
    title: str
    description: str


@dataclass
class IngestResult:
    source_type: SourceType
    source_ref: str
    doc_hash: str
    raw_text: str
    requirement_candidates: list[RequirementCandidate]


def compute_doc_hash(text: str) -> str:
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def extract_requirement_candidates(raw_text: str, source_prefix: str = "PDF") -> list[RequirementCandidate]:
    """Heuristic extraction of requirement candidates from raw document text."""
    candidates: list[RequirementCandidate] = []
    seen_ids: set[str] = set()

    for match in REQ_ID_PATTERN.finditer(raw_text):
        req_id = match.group(1).upper().replace("_", "-")
        if req_id in seen_ids:
            continue
        start = match.start()
        end = min(start + 500, len(raw_text))
        snippet = raw_text[start:end].strip()
        lines = [ln.strip() for ln in snippet.splitlines() if ln.strip()]
        title = lines[0][:120] if lines else req_id
        description = snippet[:1000]
        candidates.append(RequirementCandidate(id=req_id, title=title, description=description))
        seen_ids.add(req_id)

    for match in SHALL_MUST_PATTERN.finditer(raw_text):
        text = match.group(1).strip()
        if len(text) < 20:
            continue
        seq = len(candidates) + 1
        req_id = f"REQ-{source_prefix}-{seq:03d}"
        while req_id in seen_ids:
            seq += 1
            req_id = f"REQ-{source_prefix}-{seq:03d}"
        title = text.split(".")[0][:120]
        candidates.append(RequirementCandidate(id=req_id, title=title, description=text[:1000]))
        seen_ids.add(req_id)

    if not candidates:
        for idx, match in enumerate(NUMBERED_SECTION.finditer(raw_text), start=1):
            section_num, body = match.group(1), match.group(2).strip()
            if len(body) < 30:
                continue
            req_id = f"REQ-{source_prefix}-{idx:03d}"
            title = body.split(".")[0][:120]
            candidates.append(
                RequirementCandidate(id=req_id, title=title, description=body[:1000])
            )
            if idx >= 50:
                break

    return candidates
