"""Entry point for the Reddit Agent — accepts keywords, runs the pipeline, writes output."""

import argparse
import logging
import sys

from reddit_agent.config import settings
from reddit_agent.graph import build_graph
from reddit_agent.report.formatter import write_markdown, write_json
from reddit_agent.state import RedditAgentState


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the agent."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def run(
    keywords: list[str],
    max_threads_per_keyword: int | None = None,
    output_dir: str = "./output",
) -> RedditAgentState:
    """Run the full Reddit agent pipeline.

    Args:
        keywords: Keywords to search Reddit (via Google) for.
        max_threads_per_keyword: Cap on threads kept per keyword.
        output_dir: Directory for output files.

    Returns:
        Final pipeline state.
    """
    logger = logging.getLogger(__name__)

    max_threads = max_threads_per_keyword or settings.max_threads_per_keyword

    logger.info("Starting Reddit discovery for %d keyword(s): %s", len(keywords), ", ".join(keywords))

    graph = build_graph()

    initial_state: RedditAgentState = {
        "keywords": keywords,
        "max_threads_per_keyword": max_threads,
        "personas": [],
        "reddit_bearer_token": "",
        "exclude_thread_ids": [],
        "instructions": "",
        "results": [],
        "final_report": None,
        "errors": [],
    }

    state = graph.invoke(initial_state)
    logger.info("Pipeline complete. %d threads, %d errors.", len(state["results"]), len(state["errors"]))

    md_path = write_markdown(state["final_report"], output_dir)
    json_path = write_json(state["results"], keywords, output_dir)
    logger.info("Report saved to %s", md_path)
    logger.info("Data saved to %s", json_path)

    if state["errors"]:
        logger.warning("Completed with %d errors:", len(state["errors"]))
        for err in state["errors"]:
            logger.warning("  - %s", err)

    return state


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Reddit Agent — Google-driven Reddit thread discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m reddit_agent.main --keywords "system design interview" "grokking the coding interview"
  python -m reddit_agent.main --keywords "leetcode patterns" --max-threads 5 --output ./reports
        """,
    )
    parser.add_argument(
        "--keywords", required=True, nargs="+",
        help="Keywords to search for (space-separated, use quotes for multi-word)",
    )
    parser.add_argument(
        "--max-threads", type=int, default=None,
        help="Max threads to keep per keyword (default: from config)",
    )
    parser.add_argument(
        "--output", default="./output",
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose/debug logging",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    try:
        state = run(args.keywords, args.max_threads, args.output)
        print(f"\nReport saved to {args.output}/reddit_report.md")
        print(f"Data saved to {args.output}/report_data.json")
        if state["errors"]:
            print(f"\nCompleted with {len(state['errors'])} errors (see report for details)")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
