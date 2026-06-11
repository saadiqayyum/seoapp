"""Final report assembly — builds the markdown report from analyzed threads.

Unlike the SEO agent (which asks Gemini to write the prose), the per-thread analysis is
already structured by the analyze node, so this node just composes deterministic markdown.
Threads are grouped by the keyword that surfaced them. Mirrors the trailing `# Errors`
block convention from seo_agent/report/synthesiser.py.
"""

import logging

from reddit_agent.state import ThreadComment, ThreadData

logger = logging.getLogger(__name__)


def _format_comments(comments: list[ThreadComment]) -> str:
    if not comments:
        return ""
    lines = ["", "**Top comments:**"]
    for c in comments[:3]:
        body = (c.get("body") or "").strip().replace("\n", " ")
        if len(body) > 240:
            body = body[:240] + "..."
        lines.append(f"- _u/{c.get('author', '[deleted]')} ({c.get('score', 0)})_: {body}")
    return "\n".join(lines)


def _format_thread(thread: ThreadData) -> str:
    title = thread.get("title") or "(untitled)"
    url = thread.get("url", "")
    sub = thread.get("subreddit", "")
    score = thread.get("score", 0)
    ncom = thread.get("num_comments", 0)

    parts = [f"### [{title}]({url})"]
    parts.append(f"r/{sub} · {score} upvotes · {ncom} comments")

    if thread.get("summary"):
        parts.append(f"\n**Summary:** {thread['summary']}")
    if thread.get("relevance"):
        parts.append(f"\n**Relevance:** {thread['relevance']}")

    tps = thread.get("talking_points", [])
    if tps:
        parts.append("\n**Talking points:**")
        parts.extend(f"- {t}" for t in tps)

    if thread.get("suggested_reply"):
        tone = thread.get("tone", "")
        tone_label = f" ({tone})" if tone else ""
        parts.append(f"\n**Suggested reply{tone_label}:**")
        parts.append("\n> " + thread["suggested_reply"].replace("\n", "\n> "))

    comments_md = _format_comments(thread.get("top_comments", []))
    if comments_md:
        parts.append(comments_md)

    return "\n".join(parts)


def synthesise_report_node(state: dict) -> dict:
    """LangGraph node: assemble the final markdown report grouped by keyword."""
    results: list[ThreadData] = state.get("results", [])
    errors = state.get("errors", [])
    keywords = state.get("keywords", [])

    header = "# Reddit Thread Report\n\n"
    header += f"Keywords: {', '.join(keywords)}\n\n"
    header += f"Found **{len(results)}** relevant thread(s).\n"

    if not results:
        body = "\n\n_No relevant Reddit threads were found for these keywords._"
        final = header + body
        if errors:
            final += "\n\n---\n\n# Errors\n\n" + "\n".join(f"- {e}" for e in errors)
        return {**state, "final_report": final, "errors": errors}

    # Group threads by the keyword that surfaced them, preserving keyword order.
    by_keyword: dict[str, list[ThreadData]] = {}
    for t in results:
        by_keyword.setdefault(t.get("keyword", ""), []).append(t)

    sections: list[str] = []
    ordered = [k for k in keywords if k in by_keyword] + [
        k for k in by_keyword if k not in keywords
    ]
    for kw in ordered:
        threads = by_keyword.get(kw, [])
        if not threads:
            continue
        sections.append(f"## Keyword: \"{kw}\" ({len(threads)} thread(s))")
        sections.extend(_format_thread(t) for t in threads)

    final = header + "\n\n---\n\n" + "\n\n---\n\n".join(sections)

    if errors:
        final += "\n\n---\n\n# Errors\n\n" + "\n".join(f"- {e}" for e in errors)

    logger.info("Report assembled (%d chars, %d threads)", len(final), len(results))
    return {**state, "final_report": final, "errors": errors}
