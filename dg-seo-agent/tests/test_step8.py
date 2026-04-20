"""Test Step 8: tools/backlinks.py — backlink gap analysis via Moz API.

Unit tests with mocked Moz responses + one live test.
"""

from unittest.mock import patch

from seo_agent.cache.manager import clear_cache
from seo_agent.tools.backlinks import (
    find_backlink_gaps,
    find_backlink_gaps_node,
)


def setup_function():
    clear_cache()


# ── Mock data ────────────────────────────────────────────────────────────

# Your site links
YOUR_LINKS = {
    "results": [
        {"root_domain": "blogA.com", "domain_authority": 40},
        {"root_domain": "newssite.com", "domain_authority": 70},
        {"root_domain": "forum1.com", "domain_authority": 25},
    ]
}

# Competitor 1 links
COMP1_LINKS = {
    "results": [
        {"root_domain": "blogA.com", "domain_authority": 40},
        {"root_domain": "bigpub.com", "domain_authority": 85},
        {"root_domain": "techblog.com", "domain_authority": 60},
        {"root_domain": "directory.com", "domain_authority": 30},
    ]
}

# Competitor 2 links
COMP2_LINKS = {
    "results": [
        {"root_domain": "bigpub.com", "domain_authority": 85},
        {"root_domain": "techblog.com", "domain_authority": 60},
        {"root_domain": "review-site.com", "domain_authority": 50},
    ]
}

# Competitor 3 links
COMP3_LINKS = {
    "results": [
        {"root_domain": "random.com", "domain_authority": 20},
        {"root_domain": "bigpub.com", "domain_authority": 85},
    ]
}


def _mock_cached_call(fn, *args, **kwargs):
    """Intercept cached_call — drop fn and route based on Moz endpoint + target."""
    endpoint, body, moz_id, moz_secret = args
    target = body.get("target", body.get("targets", [""])[0])

    if endpoint == "url_metrics":
        return {"results": [{"domain_authority": 45}]}

    link_map = {
        "mysite.com": YOUR_LINKS,
        "competitor1.com": COMP1_LINKS,
        "competitor2.com": COMP2_LINKS,
        "competitor3.com": COMP3_LINKS,
    }
    return link_map.get(target, {"results": []})


# ── Unit tests ───────────────────────────────────────────────────────────


def test_find_backlink_gaps_basic():
    """Should find domains linking to 2+ competitors but not to you."""
    with patch("seo_agent.tools.backlinks.cached_call", side_effect=_mock_cached_call):
        gaps = find_backlink_gaps(
            "mysite.com",
            ["competitor1.com", "competitor2.com", "competitor3.com"],
        )

    domains = [g["domain"] for g in gaps]

    # bigpub.com links to all 3 competitors but not you — should be #1
    assert "bigpub.com" in domains
    # techblog.com links to 2 competitors but not you
    assert "techblog.com" in domains
    # blogA.com links to you AND competitor1 — should NOT be in gaps
    assert "bloga.com" not in domains
    # directory.com only links to 1 competitor — should NOT be in gaps
    assert "directory.com" not in domains


def test_find_backlink_gaps_sorted_by_da():
    """Results should be sorted by domain authority (highest first)."""
    with patch("seo_agent.tools.backlinks.cached_call", side_effect=_mock_cached_call):
        gaps = find_backlink_gaps(
            "mysite.com",
            ["competitor1.com", "competitor2.com", "competitor3.com"],
        )

    assert len(gaps) >= 2
    assert gaps[0]["domain_authority"] >= gaps[1]["domain_authority"]
    assert gaps[0]["domain"] == "bigpub.com"  # DA 85


def test_find_backlink_gaps_includes_linked_count():
    """Each gap should report how many competitors link to it."""
    with patch("seo_agent.tools.backlinks.cached_call", side_effect=_mock_cached_call):
        gaps = find_backlink_gaps(
            "mysite.com",
            ["competitor1.com", "competitor2.com", "competitor3.com"],
        )

    bigpub = next(g for g in gaps if g["domain"] == "bigpub.com")
    assert bigpub["linked_competitors"] == 3

    techblog = next(g for g in gaps if g["domain"] == "techblog.com")
    assert techblog["linked_competitors"] == 2


def test_find_backlink_gaps_limits_competitors():
    """Should only check max_competitors competitors."""
    call_targets = []

    def tracking_mock(fn, *args, **kwargs):
        endpoint, body, moz_id, moz_secret = args
        target = body.get("target", "")
        if target:
            call_targets.append(target)
        return _mock_cached_call(fn, *args, **kwargs)

    with patch("seo_agent.tools.backlinks.cached_call", side_effect=tracking_mock):
        find_backlink_gaps(
            "mysite.com",
            ["competitor1.com", "competitor2.com", "competitor3.com"],
            max_competitors=2,
        )

    # Should only check 2 competitors + your own domain
    comp_calls = [t for t in call_targets if t != "mysite.com"]
    assert len(comp_calls) == 2


def test_find_backlink_gaps_no_competitors():
    """Empty competitor list should return empty gaps."""
    with patch("seo_agent.tools.backlinks.cached_call", side_effect=_mock_cached_call):
        gaps = find_backlink_gaps("mysite.com", [])

    assert gaps == []


def test_find_backlink_gaps_handles_api_error():
    """API error on one competitor should not crash the whole analysis."""
    call_n = {"n": 0}

    def error_mock(fn, *args, **kwargs):
        endpoint, body, moz_id, moz_secret = args
        target = body.get("target", "")
        if target == "competitor2.com":
            raise Exception("Moz API rate limit")
        return _mock_cached_call(fn, *args, **kwargs)

    with patch("seo_agent.tools.backlinks.cached_call", side_effect=error_mock):
        gaps = find_backlink_gaps(
            "mysite.com",
            ["competitor1.com", "competitor2.com"],
        )

    # Should still return results from competitor1 (though none meet 2+ threshold alone)
    assert isinstance(gaps, list)


def test_node_skips_when_no_moz_keys():
    """Node should gracefully skip when Moz keys are not configured."""
    with patch("seo_agent.tools.backlinks.settings") as mock_settings:
        mock_settings.moz_access_id = ""
        mock_settings.moz_secret_key = ""

        state = {
            "target_domain": "https://mysite.com",
            "keywords": ["seo tools"],
            "results": [{
                "keyword": "seo tools",
                "your_url": "https://mysite.com/seo",
                "your_rank": 5,
                "your_page": 1,
                "top_competitors": [
                    {"rank": 1, "url": "https://comp1.com", "title": "C1", "domain": "comp1.com"},
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

        new_state = find_backlink_gaps_node(state)

    assert new_state["results"][0]["backlink_gap"] == []
    assert len(new_state["errors"]) == 0


def test_node_populates_backlink_gap():
    """Node should populate backlink_gap as formatted strings."""
    with patch("seo_agent.tools.backlinks.settings") as mock_settings, \
         patch("seo_agent.tools.backlinks.cached_call", side_effect=_mock_cached_call):
        mock_settings.moz_access_id = "test-id"
        mock_settings.moz_secret_key = "test-secret"

        state = {
            "target_domain": "https://mysite.com",
            "keywords": ["seo tools"],
            "results": [{
                "keyword": "seo tools",
                "your_url": "https://mysite.com/seo",
                "your_rank": 5,
                "your_page": 1,
                "top_competitors": [
                    {"rank": 1, "url": "https://competitor1.com/p", "title": "C1", "domain": "competitor1.com"},
                    {"rank": 2, "url": "https://competitor2.com/p", "title": "C2", "domain": "competitor2.com"},
                    {"rank": 3, "url": "https://competitor3.com/p", "title": "C3", "domain": "competitor3.com"},
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

        new_state = find_backlink_gaps_node(state)

    gaps = new_state["results"][0]["backlink_gap"]
    assert len(gaps) >= 2
    assert "bigpub.com" in gaps[0]
    assert "DA:" in gaps[0]


# ── Live test ────────────────────────────────────────────────────────────


def test_live_backlink_gaps():
    """Live test: check backlink gap between two known domains.

    Run with: pytest tests/test_step8.py::test_live_backlink_gaps -v -s
    """
    from seo_agent.config import settings

    if not settings.moz_access_id or not settings.moz_secret_key:
        import pytest
        pytest.skip("MOZ credentials not set — skipping live test")

    gaps = find_backlink_gaps(
        "python.org",
        ["nodejs.org", "ruby-lang.org", "go.dev"],
        max_competitors=2,
    )

    print(f"\n  Backlink gaps found: {len(gaps)}")
    for i, gap in enumerate(gaps[:10], 1):
        print(f"    {i}. {gap['domain']} (DA: {gap['domain_authority']:.0f}, "
              f"links to {gap['linked_competitors']} competitors)")
