"""MongoDB access — two separate databases, lazily connected.

* source DB (``MONGO_URI``)     — read-only: articles + documents.
* app DB    (``APP_MONGO_URI``) — read/write: blog_suggestions ("Mongo B").

Connections are created on first use and cached at module level so the graph
(and ``langgraph dev``) reuse a single client per process.
"""

import logging
from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from blog_agent.config import settings

logger = logging.getLogger(__name__)

_source_client: MongoClient | None = None
_app_client: MongoClient | None = None


def _default_db(client: MongoClient, uri: str, which: str) -> Database:
    """The DB named in the URI path (…/dbname)."""
    try:
        return client.get_default_database()
    except Exception:
        raise RuntimeError(
            f"No database in the {which} URI. Add it to the path (…/dbname). URI={uri!r}"
        )


def source_db() -> Database:
    """Read-only source DB (articles + documents)."""
    global _source_client
    if not settings.mongo_uri:
        raise RuntimeError("MONGO_URI is not set — cannot read blogs.")
    if _source_client is None:
        logger.info("Connecting to source MongoDB (read-only)…")
        _source_client = MongoClient(settings.mongo_uri, tz_aware=True)
    return _default_db(_source_client, settings.mongo_uri, "source")


def app_db() -> Database:
    """Read/write system DB ("Mongo B") for suggestions."""
    global _app_client
    if not settings.app_mongo_uri:
        raise RuntimeError("APP_MONGO_URI is not set — cannot write suggestions.")
    if _app_client is None:
        logger.info("Connecting to app MongoDB (read/write)…")
        _app_client = MongoClient(settings.app_mongo_uri, tz_aware=True)
    return _default_db(_app_client, settings.app_mongo_uri, "app")


def articles() -> Collection:
    return source_db()[settings.articles_collection]


def documents() -> Collection:
    return source_db()[settings.documents_collection]


def suggestions() -> Collection:
    return app_db()[settings.suggestions_collection]


def utcnow() -> datetime:
    """Timezone-aware current time (tests can monkeypatch this)."""
    return datetime.now(timezone.utc)
