from tracemap.ingestion.base import compute_doc_hash, extract_requirement_candidates


def test_compute_doc_hash_stable():
    h1 = compute_doc_hash("hello world")
    h2 = compute_doc_hash("hello world")
    assert h1 == h2
    assert len(h1) == 64


def test_extract_requirement_candidates_shall():
    text = "REQ-101 User Authentication\nThe system shall authenticate users via password."
    candidates = extract_requirement_candidates(text, "PDF")
    assert len(candidates) >= 1
    assert any("REQ-101" in c.id for c in candidates)


def test_extract_requirement_candidates_numbered():
    text = "1 Introduction\n2 Requirements\nThe module must validate input."
    candidates = extract_requirement_candidates(text, "PDF")
    assert isinstance(candidates, list)
