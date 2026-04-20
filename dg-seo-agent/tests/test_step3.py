"""Test Step 3: tools/robots_check.py — verify robots.txt compliance checking."""

from unittest.mock import patch, MagicMock

import httpx

from seo_agent.tools.robots_check import (
    can_scrape,
    get_crawl_delay,
    clear_robots_cache,
    _get_base_url,
)


def setup_function():
    clear_robots_cache()


# ── Unit tests (no network) ─────────────────────────────────────────────


def test_get_base_url():
    assert _get_base_url("https://example.com/page/1") == "https://example.com"
    assert _get_base_url("http://sub.example.com/a/b") == "http://sub.example.com"
    assert _get_base_url("https://example.com:8080/x") == "https://example.com:8080"


def test_can_scrape_allows_when_no_robots_txt():
    """If robots.txt returns 404, we should allow scraping."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = ""

    with patch("seo_agent.tools.robots_check.httpx.get", return_value=mock_response):
        assert can_scrape("https://example.com/page") is True


def test_can_scrape_allows_when_fetch_fails():
    """If robots.txt fetch times out, we should allow scraping (permissive)."""
    with patch(
        "seo_agent.tools.robots_check.httpx.get",
        side_effect=httpx.ConnectTimeout("timeout"),
    ):
        assert can_scrape("https://example.com/page") is True


def test_can_scrape_respects_disallow():
    """If robots.txt disallows a path, we should deny scraping."""
    robots_txt = "User-agent: *\nDisallow: /private/"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = robots_txt

    with patch("seo_agent.tools.robots_check.httpx.get", return_value=mock_response):
        assert can_scrape("https://example.com/private/secret") is False
        assert can_scrape("https://example.com/public/page") is True


def test_can_scrape_respects_specific_user_agent():
    """If robots.txt specifically blocks our bot, we should deny."""
    robots_txt = "User-agent: SEOBot\nDisallow: /\n\nUser-agent: *\nAllow: /"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = robots_txt

    with patch("seo_agent.tools.robots_check.httpx.get", return_value=mock_response):
        assert can_scrape("https://example.com/page", user_agent="SEOBot") is False
        assert can_scrape("https://example.com/page", user_agent="OtherBot") is True


def test_crawl_delay_returns_value():
    robots_txt = "User-agent: *\nCrawl-delay: 5"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = robots_txt

    with patch("seo_agent.tools.robots_check.httpx.get", return_value=mock_response):
        delay = get_crawl_delay("https://example.com/page")
        assert delay == 5.0


def test_crawl_delay_returns_none_when_not_set():
    robots_txt = "User-agent: *\nAllow: /"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = robots_txt

    with patch("seo_agent.tools.robots_check.httpx.get", return_value=mock_response):
        delay = get_crawl_delay("https://example.com/page")
        assert delay is None


def test_parser_caching():
    """Second call to same domain should not fetch robots.txt again."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "User-agent: *\nAllow: /"

    with patch("seo_agent.tools.robots_check.httpx.get", return_value=mock_response) as mock_get:
        can_scrape("https://example.com/page1")
        can_scrape("https://example.com/page2")

        # Should only fetch robots.txt once for the same domain
        assert mock_get.call_count == 1


# ── Live integration test (optional, needs network) ─────────────────────


def test_live_google_robots():
    """Live test: Google's robots.txt should be fetchable.

    Run with: pytest tests/test_step3.py::test_live_google_robots -v
    """
    clear_robots_cache()
    # Google allows their homepage
    result = can_scrape("https://www.google.com/")
    assert isinstance(result, bool)
    # Google blocks /search
    blocked = can_scrape("https://www.google.com/search?q=test")
    assert blocked is False
