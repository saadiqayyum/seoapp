"""State schemas passed through the LangGraph pipeline (TypedDicts, mirrors seo_agent)."""

from typing import TypedDict


class ThreadComment(TypedDict):
    """A single top-level comment on a thread."""

    author: str
    body: str
    score: int


class ThreadData(TypedDict):
    """All collected data for a single Reddit thread."""

    keyword: str            # which input keyword surfaced this thread
    thread_id: str          # reddit base36 id (used for dedupe)
    title: str
    url: str
    subreddit: str
    author: str
    score: int
    num_comments: int
    created_utc: str
    selftext: str
    google_snippet: str     # snippet SerpAPI returned (relevance context)
    top_comments: list[ThreadComment]

    # LLM-derived (filled by analyze node)
    summary: str
    relevance: str
    suggested_reply: str
    talking_points: list[str]
    tone: str               # helpful | educational | clarification


class RedditAgentState(TypedDict):
    """Top-level state passed through the LangGraph pipeline."""

    keywords: list[str]
    max_threads_per_keyword: int
    results: list[ThreadData]
    final_report: str | None
    errors: list[str]
