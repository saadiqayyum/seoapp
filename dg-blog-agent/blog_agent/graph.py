"""LangGraph pipeline for the Blog Improver.

Graph:
    load_stale_blogs --(fan-out: one Send per blog)--> analyze_one_blog --> END
    load_stale_blogs --(no blogs)--------------------------------------> END

Each per-blog branch reads the body, asks the LLM what to improve, and persists a
suggestion. Per-blog failures are captured in ``results``/``errors`` and never
abort the run.
"""

import logging
import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from blog_agent.config import settings
from blog_agent.schema import AnalyzeResult
from blog_agent.state import BlogImproverState
from blog_agent.tools.analyze import analyze_blog
from blog_agent.tools.blog_content import get_blog_content
from blog_agent.tools.fetch_stale_blogs import load_stale_blogs_node
from blog_agent.tools.save_suggestion import save_suggestion

logger = logging.getLogger(__name__)

LOAD = "load_stale_blogs"
ANALYZE = "analyze_one_blog"


def _fan_out_by_blog(state: BlogImproverState):
    """Map edge: one Send per blog, carrying the run context each branch needs.
    Routes straight to END when there is nothing to do."""
    blogs = state.get("blogs") or []
    if not blogs:
        return END
    run_id = state.get("run_id") or str(uuid.uuid4())
    instructions = state.get("instructions", "")
    return [
        Send(ANALYZE, {"blog": blog, "run_id": run_id, "instructions": instructions})
        for blog in blogs
    ]


def _analyze_one_blog_node(state: BlogImproverState) -> dict:
    """Per-branch node: analyze one blog and persist its suggestion."""
    blog = state.get("blog")
    if not blog:
        return {"results": []}

    run_id = state.get("run_id", "")
    instructions = state.get("instructions", "")

    try:
        content, outline, _found = get_blog_content(blog.get("document_id"))
        analysis = analyze_blog(blog, content, outline, instructions)
        suggestion_id = save_suggestion(blog, analysis, run_id, content)
        result: AnalyzeResult = {
            "article_id": blog.get("article_id", ""),
            "slug": blog.get("slug", ""),
            "ok": True,
            "suggestion_id": suggestion_id,
        }
        return {"results": [result]}
    except Exception as e:
        msg = f"[analyze_one_blog] slug='{blog.get('slug')}' error: {e}"
        logger.warning(msg)
        result = {
            "article_id": blog.get("article_id", ""),
            "slug": blog.get("slug", ""),
            "ok": False,
            "error": str(e),
        }
        return {"results": [result], "errors": [msg]}


def build_graph():
    """Build and compile the Blog Improver LangGraph pipeline."""
    builder = StateGraph(BlogImproverState)
    builder.add_node(LOAD, load_stale_blogs_node)
    builder.add_node(ANALYZE, _analyze_one_blog_node)

    builder.add_edge(START, LOAD)
    builder.add_conditional_edges(LOAD, _fan_out_by_blog, [ANALYZE, END])
    builder.add_edge(ANALYZE, END)

    return builder.compile()


# Module-level compiled instance — referenced by langgraph.json as
# `./blog_agent/graph.py:graph` so `langgraph dev` can serve it.
graph = build_graph()
