"""Test Step 10: tools/internal_links.py — internal link auditor."""

import asyncio
from unittest.mock import patch

from seo_agent.cache.manager import clear_cache
from seo_agent.tools.internal_links import (
    _is_internal,
    _normalize_url,
    _extract_internal_links,
    _calculate_link_score,
    _check_anchor_relevance,
    audit_internal_links,
    audit_internal_links_node,
)


def setup_function():
    clear_cache()


# ── Mock HTML ────────────────────────────────────────────────────────────

TARGET_PAGE_HTML = """
<html>
<body>
    <h1>SEO Guide</h1>
    <a href="/blog">Blog</a>
    <a href="/pricing">Pricing</a>
    <a href="/about">About Us</a>
    <a href="https://mysite.com/tools">Our Tools</a>
    <a href="https://external.com/link">External</a>
    <a href="#section1">Anchor link</a>
    <a href="javascript:void(0)">JS link</a>
    <a href="/faq">Click here</a>
</body>
</html>
"""

HOMEPAGE_HTML = """
<html>
<body>
    <nav>
        <a href="/seo-guide">SEO Guide</a>
        <a href="/blog">Blog</a>
        <a href="/pricing">Pricing</a>
    </nav>
    <a href="/seo-guide">Learn about SEO tools</a>
    <a href="/other-page">Other</a>
    <a href="/another-page">Another</a>
</body>
</html>
"""

OTHER_PAGE_HTML = """
<html>
<body>
    <p>Check our <a href="/seo-guide">complete SEO guide</a> for details.</p>
    <a href="/blog">Blog</a>
</body>
</html>
"""

ORPHAN_PAGE_HTML = """
<html>
<body>
    <h1>Lonely Page</h1>
    <p>No internal links at all.</p>
</body>
</html>
"""


# ── Unit tests: helpers ──────────────────────────────────────────────────


def test_is_internal():
    base = "https://mysite.com/page"
    assert _is_internal("/blog", base) is True
    assert _is_internal("./page2", base) is True
    assert _is_internal("https://mysite.com/other", base) is True
    assert _is_internal("https://external.com/page", base) is False
    assert _is_internal("#section", base) is False
    assert _is_internal("javascript:void(0)", base) is False
    assert _is_internal("mailto:a@b.com", base) is False
    assert _is_internal("", base) is False


def test_normalize_url():
    base = "https://mysite.com/page"
    assert _normalize_url("/blog", base) == "https://mysite.com/blog"
    assert _normalize_url("/page#section", base) == "https://mysite.com/page"
    assert _normalize_url("/page?q=1", base) == "https://mysite.com/page"
    assert _normalize_url("https://mysite.com/page/", base) == "https://mysite.com/page"


def test_extract_internal_links():
    links = _extract_internal_links(TARGET_PAGE_HTML, "https://mysite.com/seo-guide")

    urls = [l["url"] for l in links]
    anchors = [l["anchor_text"] for l in links]

    # Should include relative and same-domain links
    assert "https://mysite.com/blog" in urls
    assert "https://mysite.com/pricing" in urls
    assert "https://mysite.com/about" in urls
    assert "https://mysite.com/tools" in urls
    # Should NOT include external, anchor, or JS links
    assert not any("external.com" in u for u in urls)
    # Should NOT include self-link
    assert "https://mysite.com/seo-guide" not in urls
    # Anchor text should be captured
    assert "Blog" in anchors


def test_extract_internal_links_empty():
    links = _extract_internal_links("<html><body><p>No links</p></body></html>", "https://example.com")
    assert links == []


def test_calculate_link_score():
    # Good page: 10 outgoing, 5 incoming, 3/5 relevant anchors
    score = _calculate_link_score(10, 5, 3, 5)
    assert score > 0.7

    # Bad page: 0 outgoing, 0 incoming
    score = _calculate_link_score(0, 0, 0, 0)
    assert score == 0.0

    # Moderate: 5 outgoing, 2 incoming, 1/2 relevant
    score = _calculate_link_score(5, 2, 1, 2)
    assert 0.3 < score < 0.7


def test_check_anchor_relevance():
    assert _check_anchor_relevance("SEO tools guide", "seo tools") is True
    assert _check_anchor_relevance("Our complete SEO guide", "seo tools") is True
    assert _check_anchor_relevance("Click here", "seo tools") is False
    assert _check_anchor_relevance("", "seo tools") is False
    assert _check_anchor_relevance("Some text", "") is False


# ── Unit tests: audit function ───────────────────────────────────────────


def test_audit_internal_links_good_page():
    """Page with decent internal links should get reasonable score."""
    pages = {
        "https://mysite.com/seo-guide": TARGET_PAGE_HTML,
        "https://mysite.com": HOMEPAGE_HTML,
        "https://mysite.com/blog": OTHER_PAGE_HTML,
        "https://mysite.com/pricing": OTHER_PAGE_HTML,
        "https://mysite.com/other-page": OTHER_PAGE_HTML,
        "https://mysite.com/another-page": OTHER_PAGE_HTML,
    }

    async def mock_cached(fn, url, **kw):
        return pages.get(url, "<html><body></body></html>")

    with patch("seo_agent.tools.internal_links.async_cached_call", side_effect=mock_cached):
        result = asyncio.run(
            audit_internal_links("https://mysite.com/seo-guide", "seo tools", "https://mysite.com")
        )

    assert result["score"] > 0
    assert result["outgoing_count"] >= 4
    assert result["incoming_count"] >= 2  # Homepage links to it
    assert isinstance(result["issues"], list)


def test_audit_internal_links_orphan_page():
    """Page with no links should get low score and issues."""

    async def mock_cached(fn, url, **kw):
        if "orphan" in url:
            return ORPHAN_PAGE_HTML
        return "<html><body></body></html>"

    with patch("seo_agent.tools.internal_links.async_cached_call", side_effect=mock_cached):
        result = asyncio.run(
            audit_internal_links("https://mysite.com/orphan", "seo tools", "https://mysite.com")
        )

    assert result["score"] == 0.0
    assert result["outgoing_count"] == 0
    assert any("zero internal links" in i for i in result["issues"])


def test_audit_internal_links_generic_anchors():
    """Should flag generic anchor text like 'click here'."""
    pages = {
        "https://mysite.com/page": TARGET_PAGE_HTML,  # Has "Click here" anchor
        "https://mysite.com": "<html><body></body></html>",
    }

    async def mock_cached(fn, url, **kw):
        return pages.get(url, "<html><body></body></html>")

    with patch("seo_agent.tools.internal_links.async_cached_call", side_effect=mock_cached):
        result = asyncio.run(
            audit_internal_links("https://mysite.com/page", "seo", "https://mysite.com")
        )

    assert any("generic anchor text" in i for i in result["issues"])


def test_audit_internal_links_fetch_error():
    """Should handle fetch errors gracefully."""

    async def mock_cached(fn, url, **kw):
        raise Exception("Connection refused")

    with patch("seo_agent.tools.internal_links.async_cached_call", side_effect=mock_cached):
        result = asyncio.run(
            audit_internal_links("https://mysite.com/page", "seo", "https://mysite.com")
        )

    assert result["score"] == 0.0
    assert any("Could not fetch" in i for i in result["issues"])


# ── Node test ────────────────────────────────────────────────────────────


def test_audit_internal_links_node():
    """LangGraph node should populate internal_link_score and issues."""
    pages = {
        "https://mysite.com/seo": TARGET_PAGE_HTML,
        "https://mysite.com": HOMEPAGE_HTML,
    }

    async def mock_cached(fn, url, **kw):
        return pages.get(url, "<html><body></body></html>")

    state = {
        "target_domain": "https://mysite.com",
        "keywords": ["seo tools"],
        "results": [{
            "keyword": "seo tools",
            "your_url": "https://mysite.com/seo",
            "your_rank": 5,
            "your_page": 1,
            "top_competitors": [],
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

    with patch("seo_agent.tools.internal_links.async_cached_call", side_effect=mock_cached):
        new_state = audit_internal_links_node(state)

    kw = new_state["results"][0]
    assert isinstance(kw["internal_link_score"], float)
    assert isinstance(kw["internal_link_issues"], list)
    assert len(new_state["errors"]) == 0


def test_node_handles_errors():
    """Node should catch errors per keyword."""

    async def mock_error(fn, url, **kw):
        raise Exception("Network error")

    state = {
        "target_domain": "https://mysite.com",
        "keywords": ["seo tools"],
        "results": [{
            "keyword": "seo tools",
            "your_url": "https://mysite.com/seo",
            "your_rank": 5,
            "your_page": 1,
            "top_competitors": [],
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

    with patch("seo_agent.tools.internal_links.async_cached_call", side_effect=mock_error):
        new_state = audit_internal_links_node(state)

    # Error should be caught, not crash
    assert len(new_state["errors"]) == 0  # fetch error is handled inside audit_internal_links
    assert new_state["results"][0]["internal_link_score"] == 0.0


# ── Live test ────────────────────────────────────────────────────────────


def test_live_internal_links():
    """Live test: audit internal links on python.org about page.

    Run with: pytest tests/test_step10.py::test_live_internal_links -v -s
    """
    result = asyncio.run(
        audit_internal_links(
            "https://www.python.org/about/",
            "python programming",
            "https://www.python.org",
            sample_pages=5,
        )
    )

    print(f"\n  Score: {result['score']}")
    print(f"  Outgoing internal links: {result['outgoing_count']}")
    print(f"  Incoming internal links: {result['incoming_count']}")
    print(f"  Issues: {len(result['issues'])}")
    for i, issue in enumerate(result["issues"], 1):
        print(f"    {i}. {issue}")
