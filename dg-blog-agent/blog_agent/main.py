"""Entry point for the Blog Improver — pulls n stale blogs, asks the LLM what to
improve in the body, and saves each as a suggestion in the system DB."""

import argparse
import logging
import sys
import uuid

from blog_agent.config import settings
from blog_agent.graph import build_graph
from blog_agent.state import BlogImproverState


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def run(
    months_old: int,
    limit: int,
    article_types: list[str] | None = None,
    instructions: str = "",
) -> BlogImproverState:
    """Run the Blog Improver pipeline.

    Args:
        months_old: x — only blogs not updated in at least this many months.
        limit: n — max blogs to analyse.
        article_types: which article types count as blogs (default from config).
        instructions: optional override for the review brief.

    Returns:
        Final pipeline state (``results`` + ``errors``).
    """
    logger = logging.getLogger(__name__)
    run_id = str(uuid.uuid4())

    graph = build_graph()
    initial_state: BlogImproverState = {
        "run_id": run_id,
        "instructions": instructions,
        "months_old": months_old,
        "limit": limit,
        "article_types": article_types or settings.article_types,
        "blogs": [],
        "results": [],
        "errors": [],
    }

    logger.info(
        "Blog Improver run %s — %d blogs older than %d months (%s)",
        run_id, limit, months_old, ", ".join(initial_state["article_types"]),
    )
    state = graph.invoke(initial_state)

    results = state.get("results", [])
    scanned = len(state.get("blogs", []))
    suggested = sum(1 for r in results if r.get("ok"))
    failed = sum(1 for r in results if not r.get("ok"))
    logger.info(
        "Done. scanned=%d analyzed=%d suggested=%d failed=%d",
        scanned, len(results), suggested, failed,
    )
    for err in state.get("errors", []):
        logger.warning("  - %s", err)
    return state


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Blog Improver — review stale blogs and store improvement suggestions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m blog_agent.main --months 6 --limit 50
  python -m blog_agent.main --months 12 --limit 10 --types Blog
        """,
    )
    parser.add_argument(
        "--months", type=int, default=settings.months_old,
        help=f"x — blogs not updated in at least this many months (default {settings.months_old})",
    )
    parser.add_argument(
        "--limit", type=int, default=settings.blog_limit,
        help=f"n — max blogs to analyse (default {settings.blog_limit})",
    )
    parser.add_argument(
        "--types", nargs="+", default=None,
        help="Article types to include (default from config: Blog)",
    )
    parser.add_argument(
        "--instructions", default="",
        help="Optional override for the review brief.",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose/debug logging")

    args = parser.parse_args()
    setup_logging(args.verbose)

    try:
        state = run(args.months, args.limit, args.types, args.instructions)
        results = state.get("results", [])
        suggested = sum(1 for r in results if r.get("ok"))
        print(f"\nSuggested {suggested}/{len(results)} blogs (run saved to blog_suggestions).")
        if state.get("errors"):
            print(f"Completed with {len(state['errors'])} errors.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
