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


def _fetch_serp(query: str, api_key: str, num: int) -> dict:
    """Raw SerpAPI Google call — this is the function we cache."""
    params = {
        "q": query,
        "num": num,
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
    }


def discover_for_keyword(keyword: str, max_threads: int) -> list[ThreadData]:
    """Search Google (via SerpAPI) for reddit threads matching a keyword."""
    query = f"site:reddit.com {keyword}"
    # Ask for a few extra results since non-thread reddit links get filtered out.
    num = min(max(max_threads * 2, 10), 50)
    data = cached_call(_fetch_serp, query, settings.serpapi_key, num)

    results = data.get("organic_results", []) or []
    threads: list[ThreadData] = []
    for result in results:
        url = result.get("link", "") or ""
        parsed = parse_thread_url(url)
        if not parsed:
            continue
        subreddit, thread_id = parsed
        threads.append(_skeleton(keyword, thread_id, subreddit, result))
        if len(threads) >= max_threads:
            break

    logger.info("Keyword '%s': %d reddit threads from Google", keyword, len(threads))
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

    seen: set[str] = {t["thread_id"] for t in results}

    if not settings.serpapi_key:
        errors.append("[discover] SERPAPI_KEY not configured")
        return {**state, "results": results, "errors": errors}

    for keyword in keywords:
        try:
            for thread in discover_for_keyword(keyword, max_threads):
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
