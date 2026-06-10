"""Persist one blog analysis as a pending suggestion in the system DB ("Mongo B").

The ONLY collection this writes to is ``blog_suggestions`` in the app DB — never
articles/documents. The stored ``analysis`` is dumped ``by_alias`` so the document
shape stays compatible with the existing suggestion contract (camelCase fields).
"""

import logging

from bson import ObjectId
from bson.errors import InvalidId

from blog_agent.db import suggestions, utcnow
from blog_agent.schema import BlogAnalysis, BlogRef

logger = logging.getLogger(__name__)


def _maybe_object_id(value: str | None):
    """ObjectId when valid, else the raw value (so external/string ids survive)."""
    if not value:
        return None
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return value


def save_suggestion(blog: BlogRef, analysis: BlogAnalysis, run_id: str, original_content: str) -> str:
    """Insert a pending suggestion and return its id (str)."""
    now = utcnow()
    doc = {
        "runId": run_id,
        "source": "run",
        "articleId": _maybe_object_id(blog.get("article_id")),
        "slug": blog.get("slug"),
        "title": blog.get("title"),
        "articleType": blog.get("article_type"),
        "articleUpdatedAt": blog.get("updated_at"),
        "originalContent": original_content or None,
        "analysis": analysis.model_dump(by_alias=True),
        "status": "pending",
        "applied": False,
        "createdAt": now,
        "updatedAt": now,
    }
    result = suggestions().insert_one(doc)
    suggestion_id = str(result.inserted_id)
    logger.info("Saved suggestion %s for blog '%s'", suggestion_id, blog.get("slug"))
    return suggestion_id
