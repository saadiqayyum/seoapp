"""Test Step 7: tools/pagespeed.py — Google PageSpeed Insights.

Unit tests with mock API response + one live test.
"""

from unittest.mock import patch

from seo_agent.cache.manager import clear_cache
from seo_agent.tools.pagespeed import (
    _parse_pagespeed,
    get_pagespeed,
    format_pagespeed_issues,
)


def setup_function():
    clear_cache()


# ── Mock API response ────���───────────────────────────────────────────────

MOCK_PAGESPEED_RESPONSE = {
    "lighthouseResult": {
        "categories": {
            "performance": {"score": 0.72}
        },
        "audits": {
            "largest-contentful-paint": {"numericValue": 3200},
            "first-contentful-paint": {"numericValue": 1500},
            "cumulative-layout-shift": {"numericValue": 0.08},
            "total-blocking-time": {"numericValue": 150},
        },
    },
    "loadingExperience": {
        "metrics": {
            "LARGEST_CONTENTFUL_PAINT_MS": {
                "percentile": 3200,
                "category": "AVERAGE",
            },
            "CUMULATIVE_LAYOUT_SHIFT_SCORE": {
                "percentile": 8,
                "category": "FAST",
            },
            "FIRST_CONTENTFUL_PAINT_MS": {
                "percentile": 1500,
                "category": "FAST",
            },
            "INTERACTION_TO_NEXT_PAINT": {
                "percentile": 250,
                "category": "AVERAGE",
            },
            "EXPERIMENTAL_TIME_TO_FIRST_BYTE": {
                "percentile": 600,
                "category": "FAST",
            },
        }
    },
}

MOCK_PAGESPEED_SLOW = {
    "lighthouseResult": {
        "categories": {
            "performance": {"score": 0.35}
        },
        "audits": {},
    },
    "loadingExperience": {
        "metrics": {
            "LARGEST_CONTENTFUL_PAINT_MS": {
                "percentile": 6000,
                "category": "SLOW",
            },
            "CUMULATIVE_LAYOUT_SHIFT_SCORE": {
                "percentile": 25,
                "category": "SLOW",
            },
            "INTERACTION_TO_NEXT_PAINT": {
                "percentile": 500,
                "category": "SLOW",
            },
        }
    },
}

MOCK_PAGESPEED_EMPTY = {
    "lighthouseResult": {
        "categories": {},
        "audits": {},
    },
    "loadingExperience": {
        "metrics": {}
    },
}


# ── Unit tests ─────────────────────────���─────────────────────────────────


def test_parse_pagespeed_full():
    result = _parse_pagespeed(MOCK_PAGESPEED_RESPONSE)

    assert result["score"] == 72
    assert result["lcp"] == 3.2
    assert result["lcp_rating"] == "AVERAGE"
    assert result["cls"] == 0.08
    assert result["cls_rating"] == "FAST"
    assert result["fcp"] == 1.5
    assert result["fcp_rating"] == "FAST"
    assert result["inp"] == 250
    assert result["inp_rating"] == "AVERAGE"
    assert result["ttfb"] == 0.6
    assert result["ttfb_rating"] == "FAST"


def test_parse_pagespeed_empty():
    result = _parse_pagespeed(MOCK_PAGESPEED_EMPTY)

    assert result["score"] is None
    assert result["lcp"] is None
    assert result["cls"] is None


def test_parse_pagespeed_lab_fallback():
    """When no field data, should fall back to Lighthouse lab data."""
    data = {
        "lighthouseResult": {
            "categories": {"performance": {"score": 0.65}},
            "audits": {
                "largest-contentful-paint": {"numericValue": 4500},
                "cumulative-layout-shift": {"numericValue": 0.12},
            },
        },
        "loadingExperience": {"metrics": {}},
    }
    result = _parse_pagespeed(data)

    assert result["score"] == 65
    assert result["lcp"] == 4.5  # 4500ms -> 4.5s
    assert result["cls"] == 0.12


def test_get_pagespeed_no_api_key():
    """Should return None when API key is not set."""
    with patch("seo_agent.tools.pagespeed.settings") as mock_settings:
        mock_settings.pagespeed_api_key = ""
        result = get_pagespeed("https://example.com")

    assert result is None


def test_get_pagespeed_with_key():
    with patch("seo_agent.tools.pagespeed.settings") as mock_settings, \
         patch("seo_agent.tools.pagespeed.cached_call", return_value=MOCK_PAGESPEED_RESPONSE):
        mock_settings.pagespeed_api_key = "test-key"
        result = get_pagespeed("https://example.com")

    assert result["score"] == 72
    assert result["lcp"] == 3.2


def test_format_issues_good_page():
    ps = {
        "score": 95,
        "lcp": 1.8, "lcp_rating": "FAST",
        "fcp": 1.0, "fcp_rating": "FAST",
        "cls": 0.05, "cls_rating": "FAST",
        "inp": 100, "inp_rating": "FAST",
        "ttfb": 0.4, "ttfb_rating": "FAST",
    }
    issues = format_pagespeed_issues(ps)
    assert len(issues) == 0


def test_format_issues_slow_page():
    ps = {
        "score": 35,
        "lcp": 6.0, "lcp_rating": "SLOW",
        "fcp": 3.0, "fcp_rating": "SLOW",
        "cls": 0.25, "cls_rating": "SLOW",
        "inp": 500, "inp_rating": "SLOW",
        "ttfb": 1.5, "ttfb_rating": "SLOW",
    }
    issues = format_pagespeed_issues(ps)

    assert any("35/100" in i for i in issues)
    assert any("Largest Contentful Paint" in i for i in issues)
    assert any("Cumulative Layout Shift" in i for i in issues)
    assert any("Interaction to Next Paint" in i for i in issues)
    assert len(issues) >= 4


def test_format_issues_none():
    issues = format_pagespeed_issues(None)
    assert len(issues) == 1
    assert "unavailable" in issues[0]


def test_format_issues_average_ratings():
    ps = _parse_pagespeed(MOCK_PAGESPEED_RESPONSE)
    issues = format_pagespeed_issues(ps)

    # LCP is 3.2s (AVERAGE, above 2.5 threshold) — should be flagged
    assert any("Largest Contentful Paint" in i for i in issues)
    # INP is 250ms (AVERAGE, above 200 threshold) — should be flagged
    assert any("Interaction to Next Paint" in i for i in issues)


# ── Live test ───────────────────���─────────────────────────────────��──────


def test_live_pagespeed():
    """Live test: fetch PageSpeed for python.org.

    Run with: pytest tests/test_step7.py::test_live_pagespeed -v -s
    """
    from seo_agent.config import settings

    if not settings.pagespeed_api_key:
        import pytest
        pytest.skip("PAGESPEED_API_KEY not set — skipping live test")

    result = get_pagespeed("https://www.python.org/")

    assert result is not None
    assert result["score"] is not None

    print(f"\n  Performance score: {result['score']}/100")
    print(f"  LCP: {result['lcp']}s ({result['lcp_rating']})")
    print(f"  FCP: {result['fcp']}s ({result['fcp_rating']})")
    print(f"  CLS: {result['cls']} ({result['cls_rating']})")
    print(f"  INP: {result['inp']}ms ({result['inp_rating']})")
    print(f"  TTFB: {result['ttfb']}s ({result['ttfb_rating']})")

    issues = format_pagespeed_issues(result)
    print(f"\n  Issues: {len(issues)}")
    for i, issue in enumerate(issues, 1):
        print(f"    {i}. {issue}")
