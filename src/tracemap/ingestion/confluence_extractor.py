from __future__ import annotations

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from tracemap.config import get_settings
from tracemap.ingestion.base import (
    IngestResult,
    compute_doc_hash,
    extract_requirement_candidates,
)


def _extract_page_id(url: str) -> str | None:
    match = re.search(r"pageId=(\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"/pages/(\d+)", url)
    if match:
        return match.group(1)
    return None


def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def extract_from_confluence(url: str) -> IngestResult:
    try:
        from atlassian import Confluence
    except ImportError as exc:
        raise ImportError(
            "atlassian-python-api is required for Confluence ingestion. "
            "Install with: pip install atlassian-python-api"
        ) from exc

    settings = get_settings()
    if not settings.confluence_configured:
        raise ValueError(
            "Confluence credentials not configured. Set CONFLUENCE_URL, "
            "CONFLUENCE_USER, and CONFLUENCE_API_TOKEN in .env"
        )

    parsed = urlparse(url)
    base_url = settings.confluence_url.rstrip("/")
    if parsed.netloc and parsed.netloc not in base_url:
        base_url = f"{parsed.scheme}://{parsed.netloc}"

    confluence = Confluence(
        url=base_url,
        username=settings.confluence_user,
        password=settings.confluence_api_token,
        cloud=True,
    )

    page_id = _extract_page_id(url)
    if page_id:
        page = confluence.get_page_by_id(page_id, expand="body.storage")
    else:
        space_key = None
        space_match = re.search(r"/spaces/([^/]+)/", url)
        if space_match:
            space_key = space_match.group(1)
        title_match = re.search(r"/pages/\d+/([^/?#]+)", url)
        title = title_match.group(1).replace("+", " ") if title_match else None
        if not space_key or not title:
            raise ValueError(f"Cannot resolve Confluence page from URL: {url}")
        page = confluence.get_page_by_title(space_key, title, expand="body.storage")

    if not page:
        raise ValueError(f"Confluence page not found: {url}")

    html = page["body"]["storage"]["value"]
    raw_text = _html_to_text(html)
    doc_hash = compute_doc_hash(raw_text)
    candidates = extract_requirement_candidates(raw_text, source_prefix="CONF")

    return IngestResult(
        source_type="CONFLUENCE",
        source_ref=url,
        doc_hash=doc_hash,
        raw_text=raw_text,
        requirement_candidates=candidates,
    )
