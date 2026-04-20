"""Test Step 4: tools/serp.py — SERP rank checker + PAA + SERP features.

Includes:
- Unit tests with mocked SerpAPI responses (no API key needed)
- One live test that requires SERPAPI_KEY in .env (run explicitly)
"""

from unittest.mock import patch

from seo_agent.cache.manager import clear_cache
from seo_agent.tools.serp import (
    check_serp_ranking,
    check_rankings_node,
    extract_domain,
    _extract_serp_features,
)


def setup_function():
    clear_cache()


# ── Helpers ──────────────────────────────────────────────────────────────

MOCK_SERP_RESPONSE = {
    "organic_results": [
        {"link": "https://competitor1.com/page", "title": "Competitor 1 Title"},
        {"link": "https://competitor2.com/seo", "title": "Competitor 2 Title"},
        {"link": "https://competitor3.com/tools", "title": "Competitor 3 Title"},
        {"link": "https://mysite.com/seo-guide", "title": "My SEO Guide"},
        {"link": "https://competitor4.com/blog", "title": "Competitor 4 Title"},
    ],
    "related_questions": [
        {"question": "What is SEO?"},
        {"question": "How to improve SEO?"},
        {"question": "Best SEO tools?"},
    ],
    "answer_box": {"title": "Featured snippet answer"},
    "inline_videos": [{"title": "Video result"}],
    "knowledge_graph": {"title": "Knowledge panel"},
}


def _mock_fetch_serp(keyword, api_key):
    return MOCK_SERP_RESPONSE


# ── Unit tests ───────────────────────────────────────────────────────────


def test_extract_domain():
    assert extract_domain("https://example.com/page/1") == "example.com"
    assert extract_domain("http://sub.example.com/a") == "sub.example.com"
    assert extract_domain("https://example.com:8080/x") == "example.com:8080"


def test_extract_serp_features():
    features = _extract_serp_features(MOCK_SERP_RESPONSE)

    assert features["has_featured_snippet"] is True
    assert features["has_knowledge_panel"] is True
    assert features["has_video_carousel"] is True
    assert features["has_image_pack"] is False
    assert features["has_local_pack"] is False
    assert len(features["people_also_ask"]) == 3
    assert features["people_also_ask"][0] == "What is SEO?"


def test_extract_serp_features_empty():
    features = _extract_serp_features({})

    assert features["has_featured_snippet"] is False
    assert features["has_knowledge_panel"] is False
    assert features["people_also_ask"] == []


def test_check_serp_ranking_finds_target():
    with patch("seo_agent.tools.serp.cached_call", side_effect=lambda fn, *a, **kw: _mock_fetch_serp(*a, **kw)):
        result = check_serp_ranking("seo tools", "mysite.com", max_competitors=5)

    assert result["keyword"] == "seo tools"
    assert result["your_rank"] == 4
    assert result["your_url"] == "https://mysite.com/seo-guide"
    assert result["your_page"] == 1


def test_check_serp_ranking_competitors():
    with patch("seo_agent.tools.serp.cached_call", side_effect=lambda fn, *a, **kw: _mock_fetch_serp(*a, **kw)):
        result = check_serp_ranking("seo tools", "mysite.com", max_competitors=5)

    comps = result["top_competitors"]
    # Should collect competitors regardless of position relative to target
    assert len(comps) >= 3
    assert comps[0]["domain"] == "competitor1.com"
    assert comps[0]["rank"] == 1


def test_check_serp_ranking_not_found():
    with patch("seo_agent.tools.serp.cached_call", side_effect=lambda fn, *a, **kw: _mock_fetch_serp(*a, **kw)):
        result = check_serp_ranking("seo tools", "notinresults.com", max_competitors=3)

    assert result["your_rank"] is None
    assert result["your_url"] is None
    assert result["your_page"] is None
    # Should still collect competitors
    assert len(result["top_competitors"]) == 3


def test_check_serp_ranking_serp_features_included():
    with patch("seo_agent.tools.serp.cached_call", side_effect=lambda fn, *a, **kw: _mock_fetch_serp(*a, **kw)):
        result = check_serp_ranking("seo tools", "mysite.com")

    assert result["serp_features"]["has_featured_snippet"] is True
    assert len(result["serp_features"]["people_also_ask"]) == 3


def test_check_rankings_node():
    """Test the LangGraph node wrapper."""
    with patch("seo_agent.tools.serp.cached_call", side_effect=lambda fn, *a, **kw: _mock_fetch_serp(*a, **kw)):
        state = {
            "target_domain": "https://mysite.com",
            "keywords": ["seo tools"],
            "results": [],
            "final_report": None,
            "errors": [],
        }
        new_state = check_rankings_node(state)

    assert len(new_state["results"]) == 1
    kw_data = new_state["results"][0]
    assert kw_data["keyword"] == "seo tools"
    assert kw_data["your_rank"] == 4
    # Check defaults are set for later nodes
    assert kw_data["on_page_issues"] == []
    assert kw_data["missing_topics"] == []
    assert kw_data["raw_competitor_data"] == []


def test_check_rankings_node_handles_errors():
    """One keyword failing should not break others."""
    call_count = {"n": 0}

    def mock_fetch_with_error(keyword, api_key):
        call_count["n"] += 1
        if keyword == "bad keyword":
            raise Exception("API error")
        return MOCK_SERP_RESPONSE

    with patch("seo_agent.tools.serp.cached_call", side_effect=lambda fn, *a, **kw: mock_fetch_with_error(*a, **kw)):
        state = {
            "target_domain": "https://mysite.com",
            "keywords": ["bad keyword", "seo tools"],
            "results": [],
            "final_report": None,
            "errors": [],
        }
        new_state = check_rankings_node(state)

    # "seo tools" should succeed, "bad keyword" should be in errors
    assert len(new_state["results"]) == 1
    assert new_state["results"][0]["keyword"] == "seo tools"
    assert len(new_state["errors"]) == 1
    assert "bad keyword" in new_state["errors"][0]


# ── Live test (requires SERPAPI_KEY in .env) ─────────────────────────────


def test_live_serp_check():
    """Live test against SerpAPI. Run explicitly:

        pytest tests/test_step4.py::test_live_serp_check -v

    Requires SERPAPI_KEY set in .env file.
    """
    from seo_agent.config import settings

    if not settings.serpapi_key:
        import pytest
        pytest.skip("SERPAPI_KEY not set — skipping live test")

    result = check_serp_ranking("python programming", "python.org")

    assert result["keyword"] == "python programming"
    assert result["top_competitors"] is not None
    assert len(result["top_competitors"]) > 0
    assert isinstance(result["serp_features"]["has_featured_snippet"], bool)
    print(f"\n  Rank: {result['your_rank']}")
    print(f"  URL: {result['your_url']}")
    print(f"  Competitors: {len(result['top_competitors'])}")
    print(f"  PAA questions: {result['serp_features']['people_also_ask']}")
