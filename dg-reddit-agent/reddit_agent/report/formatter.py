"""Report formatter — writes final outputs as Markdown and JSON files (CLI parity)."""

import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def write_markdown(report: str | None, output_dir: str) -> str:
    """Write the final report as a Markdown file."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "reddit_report.md")

    if not report:
        report = "# Reddit Thread Report\n\n*No report was generated.*"

    with open(path, "w", encoding="utf-8") as f:
        f.write(report)

    logger.info("Markdown report written to %s", path)
    return path


def write_json(results: list[dict], keywords: list[str], output_dir: str) -> str:
    """Write structured thread data as a JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "report_data.json")

    data = {
        "keywords": keywords,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "threads": results,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info("JSON data written to %s", path)
    return path
