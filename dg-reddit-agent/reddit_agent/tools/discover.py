"""Thread discovery — Google search via SerpAPI scoped to reddit.com.

Mirrors the SerpAPI usage in seo_agent/tools/serp.py: a cached `requests.get` against
serpapi.com with engine=google. We query `site:reddit.com <keyword>` so Google surfaces
the most relevant Reddit threads, then keep only links that point at an actual thread.
"""

import logging

import requests

from reddit_agent.cache.manager import cached_call
from reddit_agent.config import settings
from reddit_agent.reddit_client import parse_thread_url
from reddit_agent.state import ThreadData

logger = logging.getLogger(__name__)


def _fetch_serp(query: str, api_key: str, num: int, start: int = 0) -> dict:
    """Raw SerpAPI Google call — this is the function we cache (per page via `start`)."""
    params = {
        "q": query,
        "num": num,
        "start": start,
        "api_key": api_key,
        "engine": "google",
    }
    response = requests.get("https://serpapi.com/search", params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def _skeleton(keyword: str, thread_id: str, subreddit: str, result: dict) -> ThreadData:
    """Build a ThreadData with only the fields known from the Google result."""
    return {
        "keyword": keyword,
        "thread_id": thread_id,
        "title": result.get("title", "") or "",
        "url": result.get("link", "") or "",
        "subreddit": subreddit,
        "author": "",
        "score": 0,
        "num_comments": 0,
        "created_utc": "",
        "selftext": "",
        "google_snippet": result.get("snippet", "") or "",
        "top_comments": [],
        "summary": "",
        "relevance": "",
        "suggested_reply": "",
        "talking_points": [],
        "tone": "",
        "assigned_user_id": "",
        "assigned_user_name": "",
        "assignment_reason": "",
    }


# Google pagination: walk up to MAX_PAGES of PAGE_SIZE results, skipping threads in
# `exclude`, until we've collected `max_threads` unseen ones. This is what lets a
# repeated keyword surface the NEXT batch instead of the same threads every time.
PAGE_SIZE = 10
MAX_PAGES = 5  # ~50 Google results — plenty of headroom over max_threads


def discover_for_keyword(
    keyword: str, max_threads: int, exclude: set[str]
) -> list[ThreadData]:
    """Search Google (via SerpAPI) for reddit threads matching a keyword.

    Paginates and skips any thread_id in `exclude`, returning up to `max_threads`
    threads not seen before.
    """
    query = f"site:reddit.com {keyword}"
    threads: list[ThreadData] = []
    picked: set[str] = set()

    for page in range(MAX_PAGES):
        data = cached_call(_fetch_serp, query, settings.serpapi_key, PAGE_SIZE, page * PAGE_SIZE)
        results = data.get("organic_results", []) or []
        if not results:
            break  # no more Google results for this keyword
        for result in results:
            url = result.get("link", "") or ""
            parsed = parse_thread_url(url)
            if not parsed:
                continue
            subreddit, thread_id = parsed
            if thread_id in exclude or thread_id in picked:
                continue
            picked.add(thread_id)
            threads.append(_skeleton(keyword, thread_id, subreddit, result))
            if len(threads) >= max_threads:
                logger.info("Keyword '%s': %d new reddit threads from Google", keyword, len(threads))
                return threads

    logger.info("Keyword '%s': %d new reddit threads from Google", keyword, len(threads))
    return threads


def discover_threads_node(state: dict) -> dict:
    """LangGraph node: discover reddit threads for every keyword via Google.

    Dedupes by thread_id across keywords (first keyword to surface a thread wins).
    Per-keyword errors are recorded and don't stop the others.
    """
    keywords = state["keywords"]
    max_threads = state.get("max_threads_per_keyword") or settings.max_threads_per_keyword
    results: list[ThreadData] = state.get("results", [])
    errors: list[str] = state.get("errors", [])

    # Seed `seen` with threads already shown for these keywords (passed in run params)
    # plus anything already in results — so repeated runs surface fresh threads.
    seen: set[str] = {t["thread_id"] for t in results}
    seen |= set(state.get("exclude_thread_ids") or [])

    if not settings.serpapi_key:
        errors.append("[discover] SERPAPI_KEY not configured")
        return {**state, "results": results, "errors": errors}

    for keyword in keywords:
        try:
            for thread in discover_for_keyword(keyword, max_threads, seen):
                if thread["thread_id"] in seen:
                    continue
                seen.add(thread["thread_id"])
                results.append(thread)
        except Exception as e:
            error_msg = f"[discover] keyword='{keyword}' error: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    logger.info("Discovered %d unique threads across %d keywords", len(results), len(keywords))
    return {**state, "results": results, "errors": errors}
