"""Test Step 13: main.py + report/formatter.py — entry point and output formatting."""

import json
import os
import tempfile

from unittest.mock import patch, MagicMock

from seo_agent.report.formatter import write_markdown, write_json, _serialize_keyword_data
from seo_agent.main import run


# ── Sample data ──────────────────────────────────────────────────────────

SAMPLE_RESULTS = [
    {
        "keyword": "seo tools",
        "your_url": "https://mysite.com/seo-tools",
        "your_rank": 8,
        "your_page": 1,
        "top_competitors": [
            {"rank": 1, "url": "https://comp1.com", "title": "C1", "domain": "comp1.com"},
        ],
        "serp_features": {
            "has_featured_snippet": True,
            "has_knowledge_panel": False,
            "has_video_carousel": False,
            "has_image_pack": False,
            "has_local_pack": False,
            "people_also_ask": ["What is SEO?"],
        },
        "on_page_issues": ["Title too short"],
        "missing_topics": ["pricing"],
        "backlink_gap": ["bigpub.com (DA: 85)"],
        "internal_link_score": 0.45,
        "internal_link_issues": ["Few incoming links"],
        "page_speed": {"score": 72, "lcp": 3.2},
        "raw_competitor_data": [{"url": "https://comp1.com", "h2": ["Features"]}],
    },
]

SAMPLE_REPORT = "# SEO Audit Report\n\nThis is the full report content."


# ── formatter tests ──────────────────────────────────────────────────────


def test_write_markdown():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_markdown(SAMPLE_REPORT, tmpdir)

        assert os.path.exists(path)
        assert path.endswith("seo_report.md")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "SEO Audit Report" in content


def test_write_markdown_none():
    """Should write a fallback message when report is None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_markdown(None, tmpdir)

        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "No report was generated" in content


def test_write_markdown_creates_dir():
    """Should create the output directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nested = os.path.join(tmpdir, "sub", "dir")
        path = write_markdown(SAMPLE_REPORT, nested)
        assert os.path.exists(path)


def test_write_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_json(SAMPLE_RESULTS, "https://mysite.com", tmpdir)

        assert os.path.exists(path)
        assert path.endswith("report_data.json")

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["domain"] == "https://mysite.com"
        assert "generated_at" in data
        assert len(data["keywords"]) == 1
        kw = data["keywords"][0]
        assert kw["keyword"] == "seo tools"
        assert kw["your_rank"] == 8
        assert kw["page_speed"]["score"] == 72


def test_write_json_includes_raw_competitor_data():
    """JSON output must include raw_competitor_data so the web-app can render it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_json(SAMPLE_RESULTS, "https://mysite.com", tmpdir)

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        kw = data["keywords"][0]
        assert "raw_competitor_data" in kw
        assert "competitor_insights" in kw
        assert "your_page_data" in kw


def test_serialize_keyword_data():
    serialized = _serialize_keyword_data(SAMPLE_RESULTS)
    assert len(serialized) == 1
    assert "raw_competitor_data" in serialized[0]
    assert "competitor_insights" in serialized[0]
    assert serialized[0]["keyword"] == "seo tools"
    assert serialized[0]["internal_link_score"] == 0.45


# ── main.run() tests ────────────────────────────────────────────────────

def _make_mock_graph(state_override=None):
    """Create a mock graph that returns pre-built state."""
    mock_graph = MagicMock()

    def mock_invoke(initial_state):
        result = {**initial_state}
        result["results"] = SAMPLE_RESULTS
        if state_override:
            result.update(state_override)
        return result

    mock_graph.invoke.side_effect = mock_invoke
    return mock_graph


def test_run_full_pipeline():
    """run() should produce both markdown and JSON output files."""
    mock_graph = _make_mock_graph()

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("seo_agent.main.build_graph", return_value=mock_graph), \
             patch("seo_agent.main.synthesise_report_node") as mock_synth:

            mock_synth.side_effect = lambda state: {
                **state,
                "final_report": SAMPLE_REPORT,
            }

            state = run("https://mysite.com", ["seo tools"], tmpdir)

        # Check output files exist
        assert os.path.exists(os.path.join(tmpdir, "seo_report.md"))
        assert os.path.exists(os.path.join(tmpdir, "report_data.json"))

        # Check state
        assert state["final_report"] is not None
        assert len(state["results"]) == 1


def test_run_normalizes_domain():
    """run() should add https:// if missing."""
    mock_graph = _make_mock_graph()

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("seo_agent.main.build_graph", return_value=mock_graph), \
             patch("seo_agent.main.synthesise_report_node") as mock_synth:

            mock_synth.side_effect = lambda state: {
                **state,
                "final_report": SAMPLE_REPORT,
            }

            state = run("mysite.com", ["seo tools"], tmpdir)

        assert state["target_domain"] == "https://mysite.com"


def test_run_with_errors():
    """run() should complete even with errors in state."""
    mock_graph = _make_mock_graph({"errors": ["[check_rankings] timeout"]})

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("seo_agent.main.build_graph", return_value=mock_graph), \
             patch("seo_agent.main.synthesise_report_node") as mock_synth:

            mock_synth.side_effect = lambda state: {
                **state,
                "final_report": SAMPLE_REPORT + "\n\n# Errors\n- timeout",
            }

            state = run("https://mysite.com", ["seo tools"], tmpdir)

        assert len(state["errors"]) >= 1
        # Files should still be written
        assert os.path.exists(os.path.join(tmpdir, "seo_report.md"))


def test_run_multiple_keywords():
    """run() should handle multiple keywords."""
    mock_graph = MagicMock()

    def mock_invoke(initial_state):
        result = {**initial_state}
        result["results"] = [
            {**SAMPLE_RESULTS[0], "keyword": kw}
            for kw in initial_state["keywords"]
        ]
        return result

    mock_graph.invoke.side_effect = mock_invoke

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("seo_agent.main.build_graph", return_value=mock_graph), \
             patch("seo_agent.main.synthesise_report_node") as mock_synth:

            mock_synth.side_effect = lambda state: {
                **state,
                "final_report": SAMPLE_REPORT,
            }

            state = run("https://mysite.com", ["seo tools", "keyword research"], tmpdir)

        assert len(state["results"]) == 2

        # JSON should have both keywords
        with open(os.path.join(tmpdir, "report_data.json"), encoding="utf-8") as f:
            data = json.load(f)
        assert len(data["keywords"]) == 2
