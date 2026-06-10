"""Read a blog body (text + outline) from the ``documents`` collection.

A missing/unresolvable document is NOT a hard error: the blog's metadata
(title/subtitle/SEO/tags) is still worth reviewing, so callers degrade to empty
content and let the analysis proceed. Read-only.
"""

import logging

from bson import ObjectId
from bson.errors import InvalidId

from blog_agent.db import documents

logger = logging.getLogger(__name__)


def _extract_section_text(section: dict) -> str:
    """Recursively pull readable text out of a section tree.

    Markdown sections carry text in ``markdown.text``; nested/collapse sections
    hold children under ``sections``. Defensive — unknown shapes are skipped.
    """
    parts: list[str] = []
    markdown = section.get("markdown")
    if isinstance(markdown, dict) and markdown.get("text"):
        parts.append(markdown["text"])

    nested = section.get("sections")
    if isinstance(nested, list):
        for child in nested:
            if isinstance(child, dict):
                parts.append(_extract_section_text(child))

    return "\n\n".join(p for p in parts if p)


def extract_document_content(latest: dict | None) -> tuple[str, list[str]]:
    """Extract (text, outline) from a web-app document's ``latestDocument``."""
    if not latest:
        return "", []

    sections = latest.get("sections") or []
    text = "\n\n".join(
        t for t in (_extract_section_text(s) for s in sections if isinstance(s, dict)) if t
    )
    outline = [
        item["title"]
        for item in (latest.get("outline") or [])
        if isinstance(item, dict) and item.get("title")
    ]
    return text, outline


def get_blog_content(document_id: str | None) -> tuple[str, list[str], bool]:
    """Fetch a blog body by ``documentId``.

    Returns ``(text, outline, found)``. ``found`` is False when the document is
    missing/unresolvable so the caller can do a metadata-only review.
    """
    if not document_id:
        return "", [], False

    try:
        oid = ObjectId(document_id)
    except (InvalidId, TypeError):
        logger.warning("Invalid documentId: %s", document_id)
        return "", [], False

    doc = documents().find_one(
        {"_id": oid}, projection={"latestDocument": 1, "draftDocuments": 1}
    )
    if not doc:
        return "", [], False

    # Prefer published content; fall back to the most recent draft.
    text, outline = extract_document_content(doc.get("latestDocument"))
    if text:
        return text, outline, True

    drafts = doc.get("draftDocuments") or []
    if drafts:
        latest_draft = drafts[-1].get("document") if isinstance(drafts[-1], dict) else None
        text, outline = extract_document_content(latest_draft)
        return text, outline, bool(text)

    return "", [], False
