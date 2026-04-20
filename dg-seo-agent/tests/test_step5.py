"""Test Step 5: tools/competitor.py — competitor page scraper.

Includes:
- Unit tests with mock HTML (no network needed)
- One live test that scrapes a real page (run explicitly)
"""

import asyncio
from unittest.mock import patch, AsyncMock

from seo_agent.cache.manager import clear_cache
from seo_agent.tools.competitor import (
    extract_domain,
    get_meta_description,
    _parse_page,
    scrape_page,
    scrape_competitors,
    analyse_competitors_node,
)


def setup_function():
    clear_cache()


# ── Mock HTML ────────────────────────────────────────────────────────────

MOCK_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Best SEO Tools in 2024 - CompetitorSite</title>
    <meta name="description" content="A comprehensive guide to the best SEO tools available today.">
    <link rel="canonical" href="https://competitor.com/seo-tools">
    <script type="application/ld+json">{"@type": "Article"}</script>
</head>
<body>
    <h1>Best SEO Tools in 2024</h1>
    <p>Here is our guide to the top SEO tools. We have reviewed dozens of tools to bring you this list.</p>

    <h2>Free SEO Tools</h2>
    <p>These tools are great for beginners who are just starting out with SEO optimization.</p>
    <a href="/other-page">Internal link</a>
    <a href="https://competitor.com/blog">Another internal</a>

    <h2>Paid SEO Tools</h2>
    <p>For professionals who need more advanced features and detailed analytics.</p>
    <a href="https://external-site.com/tool">External link</a>

    <h3>Ahrefs Review</h3>
    <p>Ahrefs is one of the most popular SEO tools on the market.</p>

    <h3>SEMrush Review</h3>
    <p>SEMrush offers a comprehensive suite of marketing tools.</p>

    <img src="tool.png" alt="SEO tool screenshot">
</body>
</html>
"""

MOCK_HTML_MINIMAL = """
<html><head></head><body><p>Hello world</p></body></html>
"""


# ── Unit tests ───────────────────────────────────────────────────────────


def test_extract_domain():
    assert extract_domain("https://example.com/page") == "example.com"
    assert extract_domain("https://sub.example.com") == "sub.example.com"
    assert extract_domain("not-a-url") == ""


def test_parse_page_full():
    data = _parse_page("https://competitor.com/seo-tools", MOCK_HTML)

    assert data["url"] == "https://competitor.com/seo-tools"
    assert "Best SEO Tools" in data["title"]
    assert "comprehensive guide" in data["meta_description"]
    assert data["h1"] == ["Best SEO Tools in 2024"]
    assert len(data["h2"]) == 2
    assert "Free SEO Tools" in data["h2"]
    assert "Paid SEO Tools" in data["h2"]
    assert len(data["h3"]) == 2
    assert data["word_count"] > 50
    assert data["has_schema"] is True
    assert data["internal_links"] >= 2
    assert data["external_links"] >= 1


def test_parse_page_minimal():
    data = _parse_page("https://example.com", MOCK_HTML_MINIMAL)

    assert data["title"] == ""
    assert data["meta_description"] == ""
    assert data["h1"] == []
    assert data["h2"] == []
    assert data["word_count"] == 2  # "Hello world"
    assert data["has_schema"] is False


def test_scrape_page_robots_blocked():
    """Pages blocked by robots.txt should return a placeholder."""

    with patch("seo_agent.tools.competitor.can_scrape", return_value=False):
        result = asyncio.run(scrape_page("https://blocked.com/page"))

    assert result["title"] == "[blocked by robots.txt]"
    assert result["word_count"] == 0


def test_scrape_page_success():
    """Successful scrape should return parsed data."""

    async def mock_cached(fn, url, **kw):
        return MOCK_HTML

    with patch("seo_agent.tools.competitor.can_scrape", return_value=True), \
         patch("seo_agent.tools.competitor.async_cached_call", side_effect=mock_cached):
        result = asyncio.run(scrape_page("https://competitor.com/seo-tools"))

    assert "Best SEO Tools" in result["title"]
    assert len(result["h2"]) == 2


def test_scrape_competitors_multiple():
    """Should scrape multiple URLs concurrently."""

    async def mock_cached(fn, url, **kw):
        return MOCK_HTML

    with patch("seo_agent.tools.competitor.can_scrape", return_value=True), \
         patch("seo_agent.tools.competitor.async_cached_call", side_effect=mock_cached):
        results = asyncio.run(scrape_competitors([
            "https://site1.com/page",
            "https://site2.com/page",
            "https://site3.com/page",
        ]))

    assert len(results) == 3
    for r in results:
        assert "Best SEO Tools" in r["title"]


def test_scrape_competitors_handles_errors():
    """Failed scrapes should return error placeholders, not crash."""
    call_n = {"n": 0}

    async def mock_cached(fn, url, **kw):
        call_n["n"] += 1
        if "bad" in url:
            raise Exception("Connection refused")
        return MOCK_HTML

    with patch("seo_agent.tools.competitor.can_scrape", return_value=True), \
         patch("seo_agent.tools.competitor.async_cached_call", side_effect=mock_cached):
        results = asyncio.run(scrape_competitors([
            "https://good-site.com/page",
            "https://bad-site.com/page",
        ]))

    assert len(results) == 2
    assert "Best SEO Tools" in results[0]["title"]
    assert "[error:" in results[1]["title"]


def test_analyse_competitors_node():
    """LangGraph node should populate raw_competitor_data."""

    async def mock_cached(fn, url, **kw):
        return MOCK_HTML

    state = {
        "target_domain": "https://mysite.com",
        "keywords": ["seo tools"],
        "results": [{
            "keyword": "seo tools",
            "your_url": "https://mysite.com/seo",
            "your_rank": 5,
            "your_page": 1,
            "top_competitors": [
                {"rank": 1, "url": "https://comp1.com/page", "title": "C1", "domain": "comp1.com"},
                {"rank": 2, "url": "https://comp2.com/page", "title": "C2", "domain": "comp2.com"},
            ],
            "serp_features": {"has_featured_snippet": False, "has_knowledge_panel": False,
                              "has_video_carousel": False, "has_image_pack": False,
                              "has_local_pack": False, "people_also_ask": []},
            "on_page_issues": [],
            "missing_topics": [],
            "backlink_gap": [],
            "internal_link_score": 0.0,
            "internal_link_issues": [],
            "page_speed": None,
            "raw_competitor_data": [],
        }],
        "final_report": None,
        "errors": [],
    }

    with patch("seo_agent.tools.competitor.can_scrape", return_value=True), \
         patch("seo_agent.tools.competitor.async_cached_call", side_effect=mock_cached):
        new_state = analyse_competitors_node(state)

    assert len(new_state["results"][0]["raw_competitor_data"]) == 2
    assert new_state["results"][0]["raw_competitor_data"][0]["h1"] == ["Best SEO Tools in 2024"]


# ── Live test (requires network) ─────────────────────────────────────────


def test_live_scrape():
    """Live test: scrape a real page.

    Run with: pytest tests/test_step5.py::test_live_scrape -v -s
    """
    result = asyncio.run(scrape_page("https://www.python.org/about/"))

    assert result["url"] == "https://www.python.org/about/"
    assert result["word_count"] > 50
    print(f"\n  Title: {result['title']}")
    print(f"  Word count: {result['word_count']}")
    print(f"  H2 headings: {len(result['h2'])}")
    print(f"  H3 headings: {len(result['h3'])}")
    print(f"  Has schema: {result['has_schema']}")
    print(f"  Internal links: {result['internal_links']}")
    print(f"  External links: {result['external_links']}")
