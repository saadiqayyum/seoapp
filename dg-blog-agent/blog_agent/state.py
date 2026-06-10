"""Shared state schema for the Blog Improver pipeline.

Run inputs (params, run id, instructions) are seeded into state at invoke time
so nodes read everything from ``state``. ``blog`` carries the per-branch item
during the Send fan-out; ``results`` / ``errors`` accumulate across branches via
concat reducers.
"""

import operator
from typing import Annotated, Optional

from typing_extensions import TypedDict

from blog_agent.schema import AnalyzeResult, BlogRef


class BlogImproverState(TypedDict, total=False):
    """Top-level state passed through the LangGraph pipeline."""

    # --- run context ---
    run_id: str
    instructions: str

    # --- workflow parameters ---
    months_old: int      # x: blogs not updated in at least this many months
    limit: int           # n: max blogs to analyse
    article_types: list[str]

    # --- working set ---
    blogs: list[BlogRef]          # loaded by the entry node (replace)
    blog: Optional[BlogRef]       # per-branch item during fan-out

    # --- accumulators (concat reducers) ---
    results: Annotated[list[AnalyzeResult], operator.add]
    errors: Annotated[list[str], operator.add]
