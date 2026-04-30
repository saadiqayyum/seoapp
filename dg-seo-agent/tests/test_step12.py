"""Test Step 12: report/synthesiser.py — LLM report generation via Gemini.

Unit tests with mocked Gemini API + one live test.
"""

from unittest.mock import patch, MagicMock

from seo_agent.report.synthesiser import (
    generate_keyword_report,
    generate_summary_report,
    synthesise_report_node,
    _format_serp_features,
    _format_paa,
    _format_competitors,
    _format_issues,
    _format_page_speed,
)


# ── Sample keyword data ─────────────────────────────────────────────────

SAMPLE_KW = {
    "keyword": "seo tools",
    "your_url": "https://mysite.com/seo-tools",
    "your_rank": 8,
    "your_page": 1,
    "top_competitors": [
        {"rank": 1, "url": "https://comp1.com/page", "title": "Best SEO Tools", "domain": "comp1.com"},
        {"rank": 2, "url": "https://comp2.com/page", "title": "Top SEO Software", "domain": "comp2.com"},
    ],
    "serp_features": {
        "has_featured_snippet": True,
        "has_knowledge_panel": False,
        "has_video_carousel": True,
        "has_image_pack": False,
        "has_local_pack": False,
        "people_also_ask": ["What is the best SEO tool?", "Are SEO tools worth it?"],
    },
    "on_page_issues": [
        "Title tag is 38 characters — too short",
        "No schema markup found",
    ],
    "missing_topics": [
        {
            "topic": "pricing comparison",
            "example_heading": "Pricing Comparison",
            "level": "H2",
            "frequency": 3,
            "source_competitors": ["https://comp1.com/page", "https://comp2.com/page"],
            "kind": "heading",
        },
        {
            "topic": "free vs paid tools",
            "example_heading": "Free vs Paid Tools",
            "level": "H2",
            "frequency": 2,
            "source_competitors": ["https://comp1.com/page", "https://comp2.com/page"],
            "kind": "heading",
        },
        {
            "topic": "What is the best SEO tool?",
            "example_heading": "What is the best SEO tool?",
            "level": "H2",
            "frequency": 0,
            "source_competitors": [],
            "kind": "paa",
        },
    ],
    "competitor_insights": [
        {
            "category": "word_count",
            "observation": "Your page has 1200 words; competitors average 2500.",
            "severity": "high",
            "recommendation": "Expand content by ~1300 words.",
            "your_value": "1200 words",
            "competitor_avg": "2500 words",
            "evidence": [
                {"competitor_url": "https://comp1.com/page", "competitor_domain": "comp1.com", "value": "2400 words"},
            ],
        },
    ],
    "your_page_data": {
        "url": "https://mysite.com/seo-tools",
        "title": "SEO Tools",
        "meta_description": "",
        "h1": ["SEO Tools"],
        "h2": ["Intro"],
        "h3": [],
        "word_count": 1200,
        "has_schema": False,
        "internal_links": 5,
        "external_links": 2,
    },
    "backlink_gap": [
        {
            "source_domain": "bigpub.com",
            "opr_score": 8.5,
            "links_to_competitors": ["https://comp1.com/page", "https://comp2.com/page"],
            "links_to_you": False,
        },
        {
            "source_domain": "techblog.com",
            "opr_score": 6.0,
            "links_to_competitors": ["https://comp1.com/page", "https://comp2.com/page"],
            "links_to_you": False,
        },
    ],
    "internal_link_score": 0.45,
    "internal_link_issues": ["Only 2 internal links point to this page"],
    "page_speed": {"score": 72, "lcp": 3.2, "lcp_rating": "AVERAGE",
                   "fcp": 1.5, "fcp_rating": "FAST", "cls": 0.05, "cls_rating": "FAST",
                   "inp": 250, "inp_rating": "AVERAGE", "ttfb": 0.6, "ttfb_rating": "FAST"},
    "raw_competitor_data": [],
}

SAMPLE_KW_NOT_RANKING = {
    **SAMPLE_KW,
    "keyword": "keyword research",
    "your_url": None,
    "your_rank": None,
    "your_page": None,
}


# ── Formatter tests ──────────────────────────────────────────────────────


def test_format_serp_features():
    result = _format_serp_features(SAMPLE_KW)
    assert "Featured Snippet: YES" in result
    assert "Video Carousel: YES" in result
    assert "Knowledge Panel" not in result


def test_format_serp_features_empty():
    kw = {**SAMPLE_KW, "serp_features": {}}
    result = _format_serp_features(kw)
    assert "No special SERP features" in result


def test_format_paa():
    result = _format_paa(SAMPLE_KW)
    assert "What is the best SEO tool?" in result
    assert "Are SEO tools worth it?" in result


def test_format_paa_empty():
    kw = {**SAMPLE_KW, "serp_features": {"people_also_ask": []}}
    result = _format_paa(kw)
    assert "None found" in result


def test_format_competitors():
    result = _format_competitors(SAMPLE_KW)
    assert "#1 comp1.com" in result
    assert "#2 comp2.com" in result


def test_format_issues():
    assert "None found" in _format_issues([])
    result = _format_issues(["Issue 1", "Issue 2"])
    assert "Issue 1" in result
    assert "Issue 2" in result


def test_format_page_speed():
    result = _format_page_speed(SAMPLE_KW)
    assert "72/100" in result
    assert "LCP" in result
    assert "3.2s" in result


def test_format_page_speed_none():
    kw = {**SAMPLE_KW, "page_speed": None}
    result = _format_page_speed(kw)
    assert "No page speed data" in result


# ── Mock helpers ─────────────────────────────────────────────────────────


def _mock_gemini_response(text: str):
    """Create a mock Gemini API response."""
    mock_response = MagicMock()
    mock_response.text = text
    return mock_response


def _make_mock_client(response_text="Mock report content"):
    """Create a mock Gemini client."""
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_gemini_response(response_text)
    return mock_client


# ── generate_keyword_report ──────────────────────────────────────────────


def test_generate_keyword_report():
    """Should call Gemini with formatted prompt and return text."""
    mock_client = _make_mock_client("## Ranking Summary\nYou rank #8 for 'seo tools'...")

    with patch("seo_agent.report.synthesiser._get_client", return_value=mock_client), \
         patch("seo_agent.report.synthesiser.settings") as mock_settings:
        mock_settings.google_api_key = "test-key"
        mock_settings.gemini_model_id = "gemini-2.0-flash"
        report = generate_keyword_report(SAMPLE_KW, "https://mysite.com")

    assert "Ranking Summary" in report
    mock_client.models.generate_content.assert_called_once()
    call_kwargs = mock_client.models.generate_content.call_args
    prompt_text = call_kwargs.kwargs["contents"]
    assert "seo tools" in prompt_text
    assert "mysite.com" in prompt_text


def test_generate_keyword_report_not_ranking():
    """Should handle keywords where we're not ranking."""
    mock_client = _make_mock_client("## Ranking Summary\nNot ranking for this keyword...")

    with patch("seo_agent.report.synthesiser._get_client", return_value=mock_client), \
         patch("seo_agent.report.synthesiser.settings") as mock_settings:
        mock_settings.google_api_key = "test-key"
        mock_settings.gemini_model_id = "gemini-2.0-flash"
        report = generate_keyword_report(SAMPLE_KW_NOT_RANKING, "https://mysite.com")

    assert "Not ranking" in report


def test_generate_summary_report():
    """Should combine keyword reports into a summary."""
    mock_client = _make_mock_client("## Top 10 Actions\n1. Fix title tags...")

    with patch("seo_agent.report.synthesiser._get_client", return_value=mock_client), \
         patch("seo_agent.report.synthesiser.settings") as mock_settings:
        mock_settings.google_api_key = "test-key"
        mock_settings.gemini_model_id = "gemini-2.0-flash"
        summary = generate_summary_report(
            ["Report 1 content", "Report 2 content"],
            "https://mysite.com",
        )

    assert "Top 10 Actions" in summary


# ── synthesise_report_node ───────────────────────────────────────────────


def test_synthesise_report_node():
    """Full node should generate per-keyword reports + summary."""
    call_count = {"n": 0}

    def mock_generate(**kwargs):
        call_count["n"] += 1
        if call_count["n"] <= 2:
            return _mock_gemini_response(f"Report for keyword {call_count['n']}")
        return _mock_gemini_response("Cross-keyword summary here")

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = mock_generate

    state = {
        "target_domain": "https://mysite.com",
        "keywords": ["seo tools", "keyword research"],
        "results": [SAMPLE_KW, SAMPLE_KW_NOT_RANKING],
        "final_report": None,
        "errors": [],
    }

    with patch("seo_agent.report.synthesiser._get_client", return_value=mock_client), \
         patch("seo_agent.report.synthesiser.settings") as mock_settings:
        mock_settings.google_api_key = "test-key"
        mock_settings.gemini_model_id = "gemini-2.0-flash"
        new_state = synthesise_report_node(state)

    assert new_state["final_report"] is not None
    assert "SEO Audit Report" in new_state["final_report"]
    assert "seo tools" in new_state["final_report"]
    assert "keyword research" in new_state["final_report"]
    assert "Cross-Keyword Summary" in new_state["final_report"]
    assert call_count["n"] == 3


def test_synthesise_node_single_keyword_no_summary():
    """Single keyword should NOT generate a cross-keyword summary."""
    mock_client = _make_mock_client("Single keyword report")

    state = {
        "target_domain": "https://mysite.com",
        "keywords": ["seo tools"],
        "results": [SAMPLE_KW],
        "final_report": None,
        "errors": [],
    }

    with patch("seo_agent.report.synthesiser._get_client", return_value=mock_client), \
         patch("seo_agent.report.synthesiser.settings") as mock_settings:
        mock_settings.google_api_key = "test-key"
        mock_settings.gemini_model_id = "gemini-2.0-flash"
        new_state = synthesise_report_node(state)

    assert "Cross-Keyword Summary" not in new_state["final_report"]
    assert mock_client.models.generate_content.call_count == 1


def test_synthesise_node_no_api_key():
    """Should log error when API key is missing."""
    state = {
        "target_domain": "https://mysite.com",
        "keywords": ["seo tools"],
        "results": [SAMPLE_KW],
        "final_report": None,
        "errors": [],
    }

    with patch("seo_agent.report.synthesiser.settings") as mock_settings:
        mock_settings.google_api_key = ""
        new_state = synthesise_report_node(state)

    assert len(new_state["errors"]) == 1
    assert "GOOGLE_API_KEY" in new_state["errors"][0]
    assert new_state["final_report"] is None


def test_synthesise_node_handles_api_error():
    """API error on one keyword should not stop others."""
    call_count = {"n": 0}

    def mock_generate(**kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise Exception("API rate limit exceeded")
        return _mock_gemini_response("Report for keyword 2")

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = mock_generate

    state = {
        "target_domain": "https://mysite.com",
        "keywords": ["seo tools", "keyword research"],
        "results": [SAMPLE_KW, SAMPLE_KW_NOT_RANKING],
        "final_report": None,
        "errors": [],
    }

    with patch("seo_agent.report.synthesiser._get_client", return_value=mock_client), \
         patch("seo_agent.report.synthesiser.settings") as mock_settings:
        mock_settings.google_api_key = "test-key"
        mock_settings.gemini_model_id = "gemini-2.0-flash"
        new_state = synthesise_report_node(state)

    assert new_state["final_report"] is not None
    assert "failed" in new_state["final_report"].lower()
    assert len(new_state["errors"]) >= 1


# ── Live test ────────────────────────────────────────────────────────────


def test_live_generate_report():
    """Live test: generate a real report with Gemini.

    Run with: pytest tests/test_step12.py::test_live_generate_report -v -s
    """
    from seo_agent.config import settings

    if not settings.google_api_key:
        import pytest
        pytest.skip("GOOGLE_API_KEY not set — skipping live test")

    report = generate_keyword_report(SAMPLE_KW, "https://mysite.com")

    assert len(report) > 200
    print(f"\n  Report length: {len(report)} chars")
    print(f"  Preview:\n{report[:500]}...")
