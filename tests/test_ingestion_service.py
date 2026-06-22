import csv
import io

from tracemap.ingestion.base import IngestResult, RequirementCandidate
from tracemap.ingestion.doors_extractor import _parse_doors_csv, extract_from_doors
from tracemap.ingestion.service import extract_dual_inputs, merge_ingest_results


def test_parse_doors_csv():
    content = "Id,Object Heading,Object Text\nREQ-1,Login,The system shall authenticate users\n"
    candidates = _parse_doors_csv(content)
    assert len(candidates) == 1
    assert candidates[0].id == "REQ-1"


def test_extract_from_doors_with_link():
    result = extract_from_doors(doors_link="doors://project/module/authentication")
    assert result.source_type == "DOORS"
    assert len(result.requirement_candidates) >= 1


def test_extract_from_doors_with_csv_bytes():
    csv_bytes = b"Id,Object Heading,Object Text\nREQ-D1,Timeout,The system must timeout sessions\n"
    result = extract_from_doors(
        doors_link="doors://project/module",
        export_bytes=csv_bytes,
        export_filename="export.csv",
    )
    assert any(c.id == "REQ-D1" for c in result.requirement_candidates)


def test_merge_ingest_results_deduplicates_ids():
    r1 = IngestResult(
        source_type="PDF",
        source_ref="/tmp/a.pdf",
        doc_hash="aaa",
        raw_text="REQ-001 shall do A",
        requirement_candidates=[
            RequirementCandidate(id="REQ-001", title="A", description="desc A"),
        ],
    )
    r2 = IngestResult(
        source_type="DOORS",
        source_ref="doors://mod",
        doc_hash="bbb",
        raw_text="REQ-002 must do C",
        requirement_candidates=[
            RequirementCandidate(id="REQ-002", title="C", description="desc C"),
            RequirementCandidate(id="REQ-001", title="dup", description="dup"),
        ],
    )
    merged = merge_ingest_results([r1, r2])
    assert len(merged.requirement_candidates) == 2
