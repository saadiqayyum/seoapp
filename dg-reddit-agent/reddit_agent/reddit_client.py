"""Thin Reddit thread reader — fetches a thread's post + top-level comments as JSON.

Ported from the TypeScript reddit-monitor client. Given a public reddit thread URL
(as surfaced by Google), it reads the `<permalink>.json` endpoint. A real User-Agent
is required (Reddit blocks generic ones); an optional bearer token (harvested from a
logged-in reddit.com session) is used when anonymous reads get 403'd.
"""

import logging
import re
import time
from urllib.parse import urlparse

import requests

from reddit_agent.config import settings

logger = logging.getLogger(__name__)

PUBLIC_BASE = "https://www.reddit.com"
REQUEST_DELAY_S = 1.0  # Reddit is strict about rate limits.
SELFTEXT_CAP = 2000

# Matches a thread URL like /r/<sub>/comments/<id>/<slug>/
_THREAD_RE = re.compile(r"/r/([^/]+)/comments/([a-z0-9]+)", re.IGNORECASE)


class RedditFetchError(Exception):
    """Raised when a thread cannot be fetched (rate limit, auth, network)."""


def parse_thread_url(url: str) -> tuple[str, str] | None:
    """Extract (subreddit, thread_id) from a reddit thread URL, or None if not a thread."""
    try:
        path = urlparse(url).path
    except Exception:
        return None
    m = _THREAD_RE.search(path)
    if not m:
        return None
    return m.group(1), m.group(2).lower()


def _headers(bearer_token: str | None = None) -> dict[str, str]:
    # Prefer a per-run token (passed in run params, rotated from the UI); fall back to env.
    token = bearer_token or settings.reddit_bearer_token
    headers = {"User-Agent": settings.reddit_user_agent}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _permalink_json_url(url: str) -> str:
    """Turn a reddit thread URL into its `.json` endpoint on www.reddit.com."""
    path = urlparse(url).path.rstrip("/")
    return f"{PUBLIC_BASE}{path}.json?raw_json=1&limit={settings.max_comments_per_thread}&depth=1"


def fetch_thread(url: str, comment_limit: int | None = None, bearer_token: str | None = None) -> dict:
    """Fetch a thread's post fields + top-level comments.

    Returns a dict:
        {
          "selftext": str,
          "author": str,
          "score": int,
          "num_comments": int,
          "created_utc": str (ISO),
          "title": str,
          "top_comments": [{"author", "body", "score"}, ...],
        }

    Raises RedditFetchError on rate-limit / auth / network failures.
    """
    if comment_limit is None:
        comment_limit = settings.max_comments_per_thread

    try:
        res = requests.get(_permalink_json_url(url), headers=_headers(bearer_token), timeout=30)
    except requests.RequestException as e:
        raise RedditFetchError(f"network error: {e}") from e
    finally:
        time.sleep(REQUEST_DELAY_S)

    if res.status_code == 429:
        raise RedditFetchError("rate-limited (429)")
    if res.status_code in (401, 403):
        raise RedditFetchError(
            f"blocked ({res.status_code}) — set REDDIT_BEARER_TOKEN for authenticated reads"
        )
    if not res.ok:
        raise RedditFetchError(f"request failed ({res.status_code})")

    try:
        listings = res.json()
    except ValueError as e:
        raise RedditFetchError(f"bad JSON: {e}") from e

    post = _extract_post(listings)
    comments = _extract_comments(listings, comment_limit)
    post["top_comments"] = comments
    return post


def _extract_post(listings: object) -> dict:
    """Pull the post fields out of listing[0]."""
    try:
        children = listings[0]["data"]["children"]
        d = children[0]["data"]
    except (KeyError, IndexError, TypeError):
        return {
            "selftext": "",
            "author": "[deleted]",
            "score": 0,
            "num_comments": 0,
            "created_utc": "",
            "title": "",
        }

    selftext = (d.get("selftext") or "")[:SELFTEXT_CAP]
    if len(d.get("selftext") or "") > SELFTEXT_CAP:
        selftext += "..."
    return {
        "selftext": selftext,
        "author": d.get("author") or "[deleted]",
        "score": int(d.get("score") or 0),
        "num_comments": int(d.get("num_comments") or 0),
        "created_utc": _iso(d.get("created_utc")),
        "title": d.get("title") or "",
    }


def _extract_comments(listings: object, limit: int) -> list[dict]:
    """Pull top-level comments out of listing[1], sorted by score desc."""
    try:
        children = listings[1]["data"]["children"]
    except (KeyError, IndexError, TypeError):
        return []

    comments = []
    for c in children:
        if c.get("kind") != "t1":
            continue
        d = c.get("data") or {}
        body = d.get("body")
        if not isinstance(body, str) or not body.strip():
            continue
        comments.append({
            "author": d.get("author") or "[deleted]",
            "body": body,
            "score": int(d.get("score") or 0),
        })

    comments.sort(key=lambda x: x["score"], reverse=True)
    return comments[:limit]


def _iso(created_utc: object) -> str:
    """Convert a reddit epoch-seconds float to an ISO-8601 string."""
    try:
        from datetime import datetime, timezone

        return datetime.fromtimestamp(float(created_utc), tz=timezone.utc).isoformat()
    except (TypeError, ValueError):
        return ""
