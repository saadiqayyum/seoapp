"""State schemas passed through the LangGraph pipeline (TypedDicts, mirrors seo_agent)."""

from typing import TypedDict


class ThreadComment(TypedDict):
    """A single top-level comment on a thread."""

    author: str
    body: str
    score: int


class Persona(TypedDict):
    """A user the agent can assign threads to. The bio is the rich matching signal
    (it describes their expertise/focus); tone is a list of reply-tone hints."""

    id: str                 # matches the frontend user id (Mongo ObjectId string)
    name: str
    tone: list[str]
    bio: str


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

    # Assignment (filled by assign_threads node)
    assigned_user_id: str
    assigned_user_name: str
    assignment_reason: str


class RedditAgentState(TypedDict):
    """Top-level state passed through the LangGraph pipeline."""

    keywords: list[str]
    max_threads_per_keyword: int
    personas: list[Persona]
    reddit_bearer_token: str  # per-run Reddit bearer token (expires ~24h); "" -> use env/anon
    exclude_thread_ids: list[str]  # thread ids already shown for these keywords (skip them)
    instructions: str  # admin-set "## Your task" prompt for analyze; "" -> built-in default
    results: list[ThreadData]
    final_report: str | None
    errors: list[str]
