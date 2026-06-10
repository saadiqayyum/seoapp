"""Entry node: load published blogs not updated within ``months_old`` months.

Reads the ``articles`` collection (source DB, read-only). Scope is locked to blog
article types and a hard limit cap (``max_blogs_per_run``) — the run cannot widen
its own reach. Oldest blogs first.
"""

import logging

from blog_agent.config import settings
from blog_agent.db import articles
from blog_agent.schema import BlogRef
from blog_agent.state import BlogImproverState
from blog_agent.tools.dates import months_ago

logger = logging.getLogger(__name__)

# Exactly the article fields a BlogRef needs.
BLOG_REF_PROJECTION = {
    "title": 1,
    "subTitle": 1,
    "slug": 1,
    "tags": 1,
    "articleType": 1,
    "seoTitle": 1,
    "seoDescription": 1,
    "documentId": 1,
    "updatedAt": 1,
}


def _blog_url(base: str, slug: str) -> str:
    return f"{(base or '').rstrip('/')}/blog/{slug}"


def _to_blog_ref(doc: dict, base: str) -> BlogRef:
    """Map a raw ``articles`` doc to the agent-facing blog reference."""
    updated = doc.get("updatedAt")
    document_id = doc.get("documentId")
    return BlogRef(
        article_id=str(doc.get("_id")),
        slug=doc.get("slug", ""),
        title=doc.get("title", ""),
        sub_title=doc.get("subTitle"),
        tags=doc.get("tags") or [],
        article_type=doc.get("articleType", ""),
        seo_title=doc.get("seoTitle"),
        seo_description=doc.get("seoDescription"),
        document_id=str(document_id) if document_id else None,
        updated_at=updated.isoformat() if hasattr(updated, "isoformat") else updated,
        url=_blog_url(base, doc.get("slug", "")),
    )


def fetch_stale_blogs(months_old: int, article_types: list[str], limit: int) -> list[BlogRef]:
    """Query the source DB for stale published blogs (oldest first)."""
    hard_cap = settings.max_blogs_per_run
    effective_limit = min(limit, hard_cap)
    cutoff = months_ago(months_old)

    cursor = (
        articles()
        .find(
            {
                "articleType": {"$in": article_types},
                "published": True,
                "updatedAt": {"$lt": cutoff},
            },
            projection=BLOG_REF_PROJECTION,
        )
        .sort("updatedAt", 1)
        .limit(effective_limit)
    )

    base = settings.site_base_url
    refs = [_to_blog_ref(doc, base) for doc in cursor]
    logger.info("Found %d stale blogs (cutoff %s)", len(refs), cutoff.isoformat())
    return refs


def load_stale_blogs_node(state: BlogImproverState) -> dict:
    """LangGraph entry node: load the stale blogs to process.

    Reads workflow parameters from state (falling back to config defaults) so the
    graph works both from ``main.py`` and from ``langgraph dev``.
    """
    months_old = state.get("months_old") or settings.months_old
    limit = state.get("limit") or settings.blog_limit
    article_types = state.get("article_types") or settings.article_types

    try:
        blogs = fetch_stale_blogs(months_old, article_types, limit)
        return {"blogs": blogs}
    except Exception as e:  # surface, never crash the graph
        msg = f"[fetch_stale_blogs] error: {e}"
        logger.error(msg)
        return {"blogs": [], "errors": [msg]}
