"""Test Step 8: tools/backlinks.py — URL-level backlink gap via SerpAPI + OpenPageRank.

The implementation calls SerpAPI for each ranking URL (your URL + each competitor
URL) to discover external pages that reference it, then scores discovered source
domains via OpenPageRank. Tests stub both APIs with side_effect dispatchers.
"""

from unittest.mock import patch

from seo_agent.cache.manager import clear_cache
from seo_agent.tools.backlinks import (
    _domain_of,
    find_backlink_gaps_for_keyword,
    find_backlink_gaps_node,
)


def setup_function():
    clear_cache()


# ── Fixtures ──────────────────────────────────────────────────────────────

YOUR_URL = "https://mysite.com/seo-tools"
COMP1_URL = "https://competitor1.com/best-seo-tools"
COMP2_URL = "https://competitor2.com/seo-tool-roundup"
COMP3_URL = "https://competitor3.com/top-seo-software"

# Source pages that "link to" each ranking URL (what SerpAPI would surface).
# Each entry is the result `link` field SerpAPI would return.
SOURCES_BY_URL: dict[str, list[str]] = {
    YOUR_URL: [
        "https://blogA.com/our-favorite-tools",      # also links to comp1
        "https://forum1.com/thread/123",
    ],
    COMP1_URL: [
        "https://blogA.com/seo-tools-comparison",    # also links to you → excluded
        "https://bigpub.com/article/seo",            # links to all 3 competitors
        "https://techblog.com/post/tools",           # links to comp1 + comp2
        "https://directory.com/listings",            # links to comp1 only
    ],
    COMP2_URL: [
        "https://bigpub.com/another/article",
        "https://techblog.com/post/tools",
        "https://review-site.com/seo-roundup",
    ],
    COMP3_URL: [
        "https://bigpub.com/third/article",
        "https://random.com/blog",
    ],
}

# OpenPageRank scores for the source domains.
OPR_SCORES = {
    "blogA.com".lower(): 4.2,
    "forum1.com": 2.5,
    "bigpub.com": 8.5,
    "techblog.com": 6.0,
    "directory.com": 3.0,
    "review-site.com": 5.0,
    "random.com": 2.0,
}


def _mock_fetch_url_linkers(target_url: str, api_key: str) -> list[str]:
    return SOURCES_BY_URL.get(target_url, [])


def _mock_fetch_opr_batch(domains: tuple[str, ...], api_key: str) -> dict[str, float]:
    return {d: OPR_SCORES.get(d.lower(), 0.0) for d in domains}


def _passthrough_cached_call(fn, *args, **kwargs):
    """Bypass the cache during tests — invoke the function directly.

    `cached_call` uses `fn.__name__` to build the cache key, which doesn't play
    nice with MagicMock side_effect; bypassing the cache keeps tests focused
    on the gap logic, not the cache wiring.
    """
    kwargs.pop("ttl_hours", None)
    return fn(*args, **kwargs)


def _patches(linkers=_mock_fetch_url_linkers, opr=_mock_fetch_opr_batch):
    return [
        patch("seo_agent.tools.backlinks.cached_call", side_effect=_passthrough_cached_call),
        patch("seo_agent.tools.backlinks._fetch_url_linkers", side_effect=linkers),
        patch("seo_agent.tools.backlinks._fetch_opr_batch", side_effect=opr),
        patch("seo_agent.tools.backlinks.settings.serpapi_key", "test-serp-key"),
        patch("seo_agent.tools.backlinks.settings.openpagerank_api_key", "test-opr-key"),
    ]


def _run_with_mocks(fn, **patch_overrides):
    patches = _patches(**patch_overrides)
    for p in patches:
        p.start()
    try:
        return fn()
    finally:
        for p in patches:
            p.stop()


# ── Helpers ───────────────────────────────────────────────────────────────


def test_domain_of_strips_scheme_and_www():
    assert _domain_of("https://www.Example.com/path?x=1") == "example.com"
    assert _domain_of("http://Foo.bar/") == "foo.bar"
    assert _domain_of("") == ""


# ── Core logic ────────────────────────────────────────────────────────────


def test_finds_domains_linking_to_competitor_urls_only():
    """bigpub.com links to all 3 competitor URLs and not yours — should appear.
    blogA.com links to your URL and comp1 — should be EXCLUDED (you already have it).
    """
    gaps = _run_with_mocks(
        lambda: find_backlink_gaps_for_keyword(YOUR_URL, [COMP1_URL, COMP2_URL, COMP3_URL])
    )
    domains = [g["source_domain"] for g in gaps]

    assert "bigpub.com" in domains
    assert "techblog.com" in domains
    assert "bloga.com" not in domains       # already linking to your URL
    assert "directory.com" in domains       # 1 competitor, but no link to you


def test_sorted_by_competitor_count_then_opr():
    """bigpub (3 comps, OPR 8.5) > techblog (2 comps, OPR 6.0) > others (1 comp)."""
    gaps = _run_with_mocks(
        lambda: find_backlink_gaps_for_keyword(YOUR_URL, [COMP1_URL, COMP2_URL, COMP3_URL])
    )

    assert gaps[0]["source_domain"] == "bigpub.com"
    assert len(gaps[0]["links_to_competitors"]) == 3
    assert gaps[0]["opr_score"] == 8.5

    assert gaps[1]["source_domain"] == "techblog.com"
    assert len(gaps[1]["links_to_competitors"]) == 2

    # Among the 1-competitor entries, the higher OPR comes first
    one_comp = [g for g in gaps if len(g["links_to_competitors"]) == 1]
    opr_seq = [g["opr_score"] for g in one_comp]
    assert opr_seq == sorted(opr_seq, reverse=True)


def test_tracks_which_competitor_urls_each_source_references():
    gaps = _run_with_mocks(
        lambda: find_backlink_gaps_for_keyword(YOUR_URL, [COMP1_URL, COMP2_URL, COMP3_URL])
    )

    techblog = next(g for g in gaps if g["source_domain"] == "techblog.com")
    assert set(techblog["links_to_competitors"]) == {COMP1_URL, COMP2_URL}


def test_each_gap_has_full_shape():
    gaps = _run_with_mocks(
        lambda: find_backlink_gaps_for_keyword(YOUR_URL, [COMP1_URL])
    )
    assert gaps  # at least one
    for g in gaps:
        assert set(g.keys()) == {
            "source_domain", "opr_score", "links_to_competitors", "links_to_you",
        }
        assert g["links_to_you"] is False
        assert isinstance(g["opr_score"], float)


def test_no_competitors_returns_empty():
    gaps = _run_with_mocks(lambda: find_backlink_gaps_for_keyword(YOUR_URL, []))
    assert gaps == []


def test_works_when_user_not_ranking():
    """No your_url means no exclusion — every competitor linker becomes a candidate."""
    gaps = _run_with_mocks(
        lambda: find_backlink_gaps_for_keyword(None, [COMP1_URL])
    )
    domains = [g["source_domain"] for g in gaps]
    # blogA.com links to comp1 and would normally be excluded — but no your_url
    assert "bloga.com" in domains


def test_per_url_serp_failure_does_not_crash():
    """A SerpAPI exception on one competitor URL should not abort the whole keyword."""

    def flaky(target_url: str, api_key: str) -> list[str]:
        if target_url == COMP2_URL:
            raise Exception("SerpAPI rate limit")
        return _mock_fetch_url_linkers(target_url, api_key)

    gaps = _run_with_mocks(
        lambda: find_backlink_gaps_for_keyword(YOUR_URL, [COMP1_URL, COMP2_URL, COMP3_URL]),
        linkers=flaky,
    )
    domains = [g["source_domain"] for g in gaps]
    # bigpub.com still appears via comp1 + comp3 even though comp2 failed
    assert "bigpub.com" in domains


def test_opr_unavailable_keeps_gaps_with_zero_score():
    """If OpenPageRank batch fails, gaps are still returned with opr_score=0."""

    def opr_failure(domains: tuple[str, ...], api_key: str) -> dict[str, float]:
        raise Exception("OPR down")

    gaps = _run_with_mocks(
        lambda: find_backlink_gaps_for_keyword(YOUR_URL, [COMP1_URL, COMP2_URL, COMP3_URL]),
        opr=opr_failure,
    )
    assert gaps, "gaps should still be returned even when OPR fails"
    # Without scores, all OPR values should be 0 — but competitor-count sort still wins
    assert gaps[0]["source_domain"] == "bigpub.com"  # 3 competitors
    assert all(g["opr_score"] == 0.0 for g in gaps)


# ── Node integration ──────────────────────────────────────────────────────


def _kw_state(your_url: str | None = YOUR_URL) -> dict:
    """Minimal state shape covering one keyword and three competitor URLs."""
    return {
        "target_domain": "https://mysite.com",
        "keywords": ["seo tools"],
        "results": [{
            "keyword": "seo tools",
            "your_url": your_url,
            "your_rank": 5 if your_url else None,
            "your_page": 1 if your_url else None,
            "top_competitors": [
                {"rank": 1, "url": COMP1_URL, "title": "C1", "domain": "competitor1.com"},
                {"rank": 2, "url": COMP2_URL, "title": "C2", "domain": "competitor2.com"},
                {"rank": 3, "url": COMP3_URL, "title": "C3", "domain": "competitor3.com"},
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
            "your_page_data": None,
            "competitor_insights": [],
        }],
        "final_report": None,
        "errors": [],
    }


def test_node_skips_when_serpapi_key_missing():
    with patch("seo_agent.tools.backlinks.settings.serpapi_key", ""):
        new_state = find_backlink_gaps_node(_kw_state())

    assert new_state["results"][0]["backlink_gap"] == []
    assert new_state["errors"] == []


def test_node_populates_structured_backlink_gap():
    new_state = _run_with_mocks(lambda: find_backlink_gaps_node(_kw_state()))

    gaps = new_state["results"][0]["backlink_gap"]
    assert len(gaps) >= 2

    # Top result is the structured BacklinkGap dict, not a string
    top = gaps[0]
    assert isinstance(top, dict)
    assert top["source_domain"] == "bigpub.com"
    assert top["opr_score"] == 8.5
    assert len(top["links_to_competitors"]) == 3


def test_node_handles_keyword_with_no_competitors():
    state = _kw_state()
    state["results"][0]["top_competitors"] = []

    new_state = _run_with_mocks(lambda: find_backlink_gaps_node(state))
    assert new_state["results"][0]["backlink_gap"] == []
    assert new_state["errors"] == []


# ── Live test ─────────────────────────────────────────────────────────────


def test_live_backlink_gaps():
    """Live test against real SerpAPI + OpenPageRank.

    Run with: pytest tests/test_step8.py::test_live_backlink_gaps -v -s
    """
    import pytest
    from seo_agent.config import settings

    if not settings.serpapi_key:
        pytest.skip("SERPAPI_KEY not set — skipping live test")

    gaps = find_backlink_gaps_for_keyword(
        your_url="https://www.python.org/",
        competitor_urls=[
            "https://nodejs.org/en",
            "https://www.ruby-lang.org/en/",
        ],
    )

    print(f"\n  Backlink gaps found: {len(gaps)}")
    for i, g in enumerate(gaps[:10], 1):
        print(
            f"    {i}. {g['source_domain']} "
            f"(OPR {g['opr_score']:.1f}, links to {len(g['links_to_competitors'])} competitor URL(s))"
        )
