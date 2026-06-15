"""Thread enrichment — fetch each discovered thread's body + top comments."""

import logging

from reddit_agent.config import settings
from reddit_agent.reddit_client import RedditFetchError, fetch_thread

logger = logging.getLogger(__name__)


def fetch_threads_node(state: dict) -> dict:
    """LangGraph node: populate selftext + top_comments for each discovered thread.

    A fetch failure (403/429/network) leaves the thread's Google-derived fields intact
    and records an error — the thread is still shown, just without comments.
    """
    results = state.get("results", [])
    errors = state.get("errors", [])
    bearer_token = state.get("reddit_bearer_token") or None

    for thread in results:
        url = thread.get("url")
        if not url:
            continue
        try:
            post = fetch_thread(
                url,
                comment_limit=settings.max_comments_per_thread,
                bearer_token=bearer_token,
            )
            thread["selftext"] = post.get("selftext", "")
            thread["author"] = post.get("author", "") or thread.get("author", "")
            thread["score"] = post.get("score", 0)
            thread["num_comments"] = post.get("num_comments", 0)
            thread["created_utc"] = post.get("created_utc", "")
            thread["top_comments"] = post.get("top_comments", [])
            # Prefer the canonical reddit title if Google's was truncated.
            if post.get("title"):
                thread["title"] = post["title"]
            logger.info(
                "Fetched r/%s thread '%s' (%d comments)",
                thread.get("subreddit", "?"),
                thread.get("thread_id", "?"),
                len(thread["top_comments"]),
            )
        except RedditFetchError as e:
            error_msg = f"[fetch] thread='{thread.get('thread_id')}' error: {e}"
            logger.warning(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"[fetch] thread='{thread.get('thread_id')}' unexpected error: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    return {**state, "results": results, "errors": errors}
