"""Test Step 6: tools/onpage.py — on-page SEO auditor.

Unit tests with mock HTML + one live test.
"""

import asyncio
from unittest.mock import patch

from seo_agent.cache.manager import clear_cache
from seo_agent.tools.onpage import (
    _audit_page,
    _get_avg_competitor_word_count,
    audit_onpage_node,
)


def setup_function():
    clear_cache()


# ── Mock HTML pages ──────────────────────────────────────────────────────

GOOD_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Best SEO Tools for Small Business - Complete Guide</title>
    <meta name="description" content="Discover the best SEO tools for small business owners. Our comprehensive guide covers free and paid tools to boost your search rankings effectively today.">
    <link rel="canonical" href="https://mysite.com/seo-tools">
    <script type="application/ld+json">{"@type": "Article", "headline": "Best SEO Tools"}</script>
</head>
<body>
    <h1>Best SEO Tools for Small Business</h1>
    <p>""" + " ".join(["word"] * 2000) + """</p>
    <h2>Free SEO Tools</h2>
    <p>Some content here about free tools.</p>
    <h2>Paid SEO Tools</h2>
    <p>Some content here about paid tools.</p>
    <img src="img1.png" alt="SEO tool screenshot">
    <img src="img2.png" alt="Dashboard view">
</body>
</html>
"""

BAD_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>SEO</title>
    <meta name="description" content="Short desc.">
</head>
<body>
    <h1>Welcome</h1>
    <h1>Another H1</h1>
    <p>This is a very short page with minimal content.</p>
    <img src="img1.png">
    <img src="img2.png" alt="Has alt">
    <img src="img3.png">
</body>
</html>
"""

EMPTY_PAGE = """
<html><head></head><body><p>Hello</p></body></html>
"""


# ── Unit tests ───────────────────────────────────────────────────────────


def test_good_page_minimal_issues():
    """A well-optimized page should have few or no issues."""
    issues = _audit_page(
        "https://mysite.com/seo-tools", GOOD_PAGE, "seo tools", 1800
    )
    # Good page should pass most checks
    assert not any("Missing title" in i for i in issues)
    assert not any("Missing meta description" in i for i in issues)
    assert not any("No H1" in i for i in issues)
    assert not any("No schema" in i for i in issues)
    assert not any("missing alt" in i for i in issues)
    assert not any("No canonical" in i for i in issues)


def test_bad_page_catches_issues():
    """A poorly optimized page should trigger multiple issues."""
    issues = _audit_page(
        "https://mysite.com/page", BAD_PAGE, "seo tools", 1500
    )

    issue_text = "\n".join(issues)

    # Title too short
    assert any("too short" in i and "Title" in i for i in issues)
    # Meta desc too short
    assert any("too short" in i and "Meta" in i for i in issues)
    # Multiple H1s
    assert any("Multiple H1" in i for i in issues)
    # Keyword not in H1
    assert any("not found in H1" in i for i in issues)
    # Keyword not in title
    assert any("not found in title" in i for i in issues)
    # No schema
    assert any("No schema" in i for i in issues)
    # Missing alt tags
    assert any("missing alt" in i for i in issues)
    # No canonical
    assert any("canonical" in i.lower() for i in issues)
    # Word count below competitor average
    assert any("Word count" in i for i in issues)


def test_empty_page_catches_everything():
    """A bare-bones page should flag all missing elements."""
    issues = _audit_page(
        "https://mysite.com", EMPTY_PAGE, "test keyword", 1000
    )

    assert any("Missing title" in i or "empty" in i.lower() for i in issues)
    assert any("Missing meta description" in i for i in issues)
    assert any("No H1" in i for i in issues)
    assert any("No schema" in i for i in issues)
    assert any("No canonical" in i for i in issues)
    assert any("No H2" in i for i in issues)


def test_word_count_gap_calculation():
    """Should report the exact word gap when content is too thin."""
    issues = _audit_page(
        "https://mysite.com", BAD_PAGE, "anything", 2000
    )
    word_count_issues = [i for i in issues if "Word count" in i]
    assert len(word_count_issues) == 1
    assert "add ~" in word_count_issues[0]


def test_word_count_no_issue_when_above_threshold():
    """Should not flag word count if within 80% of competitor average."""
    issues = _audit_page(
        "https://mysite.com/seo-tools", GOOD_PAGE, "seo tools", 2000
    )
    assert not any("Word count" in i for i in issues)


def test_keyword_in_title_and_h1():
    """Should pass when keyword appears in both title and H1."""
    issues = _audit_page(
        "https://mysite.com/seo-tools", GOOD_PAGE, "seo tools", 0
    )
    assert not any("not found in title" in i for i in issues)
    assert not any("not found in H1" in i for i in issues)


def test_get_avg_competitor_word_count():
    assert _get_avg_competitor_word_count([]) == 0
    assert _get_avg_competitor_word_count([{"word_count": 0}]) == 0
    assert _get_avg_competitor_word_count([
        {"word_count": 1000},
        {"word_count": 2000},
        {"word_count": 3000},
    ]) == 2000


def test_audit_onpage_node():
    """LangGraph node should populate on_page_issues."""

    async def mock_cached(fn, url, **kw):
        return BAD_PAGE

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
            "raw_competitor_data": [{"word_count": 2000}, {"word_count": 1500}],
        }],
        "final_report": None,
        "errors": [],
    }

    with patch("seo_agent.tools.onpage.async_cached_call", side_effect=mock_cached):
        new_state = audit_onpage_node(state)

    issues = new_state["results"][0]["on_page_issues"]
    assert len(issues) > 0
    assert any("Title" in i for i in issues)


def test_audit_onpage_node_uses_homepage_when_not_ranking():
    """When your_url is None, should audit the homepage."""
    fetched_urls = []

    async def mock_cached(fn, url, **kw):
        fetched_urls.append(url)
        return GOOD_PAGE

    state = {
        "target_domain": "https://mysite.com",
        "keywords": ["seo tools"],
        "results": [{
            "keyword": "seo tools",
            "your_url": None,  # Not ranking
            "your_rank": None,
            "your_page": None,
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

    with patch("seo_agent.tools.onpage.async_cached_call", side_effect=mock_cached):
        audit_onpage_node(state)

    assert fetched_urls[0] == "https://mysite.com"


def test_audit_onpage_node_handles_errors():
    """Fetch failure should log error, not crash."""

    async def mock_cached(fn, url, **kw):
        raise Exception("Connection timeout")

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

    with patch("seo_agent.tools.onpage.async_cached_call", side_effect=mock_cached):
        new_state = audit_onpage_node(state)

    assert len(new_state["errors"]) == 1
    assert "audit_onpage" in new_state["errors"][0]


# ── Live test ────────────────────────────────────────────────────────────


def test_live_onpage_audit():
    """Live test: audit python.org about page.

    Run with: pytest tests/test_step6.py::test_live_onpage_audit -v -s
    """
    from seo_agent.tools.onpage import _fetch_page

    html = asyncio.run(_fetch_page("https://www.python.org/about/"))
    issues = _audit_page("https://www.python.org/about/", html, "python programming", 2000)

    print(f"\n  Issues found: {len(issues)}")
    for i, issue in enumerate(issues, 1):
        print(f"    {i}. {issue}")
