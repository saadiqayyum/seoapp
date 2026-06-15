"""LangGraph pipeline definition — wires the Reddit agent nodes together."""

import logging

from langgraph.graph import StateGraph, END

from reddit_agent.state import RedditAgentState
from reddit_agent.tools.discover import discover_threads_node
from reddit_agent.tools.fetch import fetch_threads_node
from reddit_agent.tools.analyze import analyze_threads_node
from reddit_agent.tools.assign import assign_threads_node
from reddit_agent.report.synthesiser import synthesise_report_node

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """Build and compile the Reddit agent LangGraph pipeline.

    Pipeline:
        discover_threads -> fetch_threads -> analyze_threads -> assign_threads
        -> synthesise_report -> END

    The report node is part of the graph (unlike the SEO agent, which runs synthesis
    after invoke()) so that callers reading the run's output_data get the final report
    directly.

    Returns:
        Compiled StateGraph ready for invocation.
    """
    graph = StateGraph(RedditAgentState)

    graph.add_node("discover_threads", discover_threads_node)
    graph.add_node("fetch_threads", fetch_threads_node)
    graph.add_node("analyze_threads", analyze_threads_node)
    graph.add_node("assign_threads", assign_threads_node)
    graph.add_node("synthesise_report", synthesise_report_node)

    graph.set_entry_point("discover_threads")
    graph.add_edge("discover_threads", "fetch_threads")
    graph.add_edge("fetch_threads", "analyze_threads")
    graph.add_edge("analyze_threads", "assign_threads")
    graph.add_edge("assign_threads", "synthesise_report")
    graph.add_edge("synthesise_report", END)

    return graph.compile()


# Module-level compiled instance — referenced by langgraph.json as
# `./reddit_agent/graph.py:graph` so `langgraph dev` can serve it.
graph = build_graph()
