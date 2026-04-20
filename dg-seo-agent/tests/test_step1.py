"""Test Step 1: state.py + config.py — verify schemas and settings load correctly."""

from seo_agent.state import (
    SEOAgentState,
    KeywordData,
    SERPFeatures,
    CompetitorData,
    CompetitorRanking,
)
from seo_agent.config import Settings


def test_serp_features_schema():
    """SERPFeatures can be created with all required fields."""
    features: SERPFeatures = {
        "has_featured_snippet": True,
        "has_knowledge_panel": False,
        "has_video_carousel": False,
        "has_image_pack": True,
        "has_local_pack": False,
        "people_also_ask": ["What is SEO?", "How to do SEO?"],
    }
    assert features["has_featured_snippet"] is True
    assert len(features["people_also_ask"]) == 2


def test_competitor_ranking_schema():
    comp: CompetitorRanking = {
        "rank": 1,
        "url": "https://example.com/page",
        "title": "Example Page",
        "domain": "example.com",
    }
    assert comp["rank"] == 1


def test_competitor_data_schema():
    data: CompetitorData = {
        "url": "https://example.com",
        "title": "Example",
        "meta_description": "A test page",
        "h1": ["Main Heading"],
        "h2": ["Sub 1", "Sub 2"],
        "h3": [],
        "word_count": 1500,
        "has_schema": True,
        "internal_links": 10,
        "external_links": 5,
    }
    assert data["word_count"] == 1500


def test_keyword_data_schema():
    kw: KeywordData = {
        "keyword": "seo tools",
        "your_url": "https://mysite.com/seo-tools",
        "your_rank": 14,
        "your_page": 2,
        "top_competitors": [],
        "serp_features": {
            "has_featured_snippet": False,
            "has_knowledge_panel": False,
            "has_video_carousel": False,
            "has_image_pack": False,
            "has_local_pack": False,
            "people_also_ask": [],
        },
        "on_page_issues": ["Title too short"],
        "missing_topics": ["pricing comparison"],
        "backlink_gap": ["moz.com"],
        "internal_link_score": 0.6,
        "internal_link_issues": ["No contextual links from blog"],
        "page_speed": {"lcp": 2.1, "cls": 0.05, "score": 78},
        "raw_competitor_data": [],
    }
    assert kw["your_rank"] == 14
    assert kw["internal_link_score"] == 0.6


def test_seo_agent_state_schema():
    state: SEOAgentState = {
        "target_domain": "https://mysite.com",
        "keywords": ["seo tools", "keyword research"],
        "results": [],
        "final_report": None,
        "errors": [],
    }
    assert len(state["keywords"]) == 2
    assert state["final_report"] is None


def test_settings_defaults():
    """Settings loads with correct defaults (no .env needed)."""
    s = Settings(
        google_api_key="test-key",
        serpapi_key="test-serp",
        _env_file=None,  # Don't read .env for this test
    )
    assert s.max_competitors == 5
    assert s.cache_ttl_hours == 24
    assert s.redis_url == "redis://localhost:6379"
    assert s.google_api_key == "test-key"


def test_settings_custom_values():
    """Settings accepts custom values."""
    s = Settings(
        anthropic_api_key="key1",
        serpapi_key="key2",
        max_competitors=10,
        cache_ttl_hours=48,
        target_domain="https://example.com",
        _env_file=None,
    )
    assert s.max_competitors == 10
    assert s.cache_ttl_hours == 48
    assert s.target_domain == "https://example.com"
