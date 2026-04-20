"""Test Step 9: tools/content_gap.py — content/topic gap analysis with thefuzz."""

from seo_agent.tools.content_gap import (
    find_missing_topics,
    find_paa_gaps,
    find_serp_feature_opportunities,
    find_content_gaps_node,
)


def _comp(url: str, h2: list[str], h3: list[str] | None = None, **extras) -> dict:
    """Build a minimal CompetitorData dict for tests."""
    return {
        "url": url,
        "title": extras.get("title", url),
        "meta_description": "",
        "h1": [],
        "h2": h2,
        "h3": h3 or [],
        "word_count": extras.get("word_count", 1000),
        "has_schema": extras.get("has_schema", False),
        "internal_links": 0,
        "external_links": 0,
    }


# ── find_missing_topics ─────────────────────────────────────────────────


def test_missing_topics_basic():
    """Topics in 2+ competitors but not yours should be flagged."""
    your = ["Introduction", "Pricing"]
    competitors = [
        _comp("https://c1.com", ["Introduction", "Features", "Comparison"]),
        _comp("https://c2.com", ["Features", "Comparison", "FAQ"]),
        _comp("https://c3.com", ["Features", "Reviews"]),
    ]
    missing = find_missing_topics(your, competitors)
    topics = [m["topic"] for m in missing]

    assert "features" in topics
    assert "comparison" in topics
    # "introduction" is in your headings — should NOT be missing
    assert "introduction" not in topics
    # "faq" and "reviews" only in 1 competitor — should NOT be flagged
    assert "faq" not in topics
    assert "reviews" not in topics


def test_missing_topics_has_attribution():
    """Every missing topic must carry source_competitors and example_heading."""
    competitors = [
        _comp("https://c1.com", ["Features", "Pricing"]),
        _comp("https://c2.com", ["Features", "Pricing"]),
    ]
    missing = find_missing_topics([], competitors)

    assert len(missing) >= 1
    for m in missing:
        assert m["source_competitors"]
        assert m["example_heading"]
        assert m["level"] in {"H2", "H3"}
        assert m["frequency"] >= 2
        assert m["kind"] == "heading"


def test_missing_topics_fuzzy_match():
    """Fuzzy matching should catch similar headings."""
    your = ["Choosing an SEO Tool", "Pricing Plans"]
    competitors = [
        _comp("https://c1.com", ["How to Choose the Right SEO Tool", "Pricing and Plans"]),
        _comp("https://c2.com", ["Choose the Best SEO Tool", "Pricing & Plans"]),
    ]
    missing = find_missing_topics(your, competitors)
    topics = [m["topic"] for m in missing]

    assert not any("choose" in t and "seo tool" in t for t in topics)
    assert not any("pricing" in t for t in topics)


def test_missing_topics_no_competitors():
    """Empty competitor list should return empty."""
    missing = find_missing_topics(["Heading 1"], [])
    assert missing == []


def test_missing_topics_you_have_nothing():
    """When you have no headings, all common competitor topics are gaps."""
    competitors = [
        _comp("https://c1.com", ["Features", "Pricing", "FAQ"]),
        _comp("https://c2.com", ["Features", "Pricing", "Reviews"]),
    ]
    missing = find_missing_topics([], competitors)
    topics = [m["topic"] for m in missing]

    assert "features" in topics
    assert "pricing" in topics


def test_missing_topics_max_20():
    """Should return at most 20 missing topics."""
    competitors = [
        _comp("https://c1.com", [f"Topic {i}" for i in range(30)]),
        _comp("https://c2.com", [f"Topic {i}" for i in range(30)]),
    ]
    missing = find_missing_topics([], competitors)
    assert len(missing) <= 20


def test_missing_topics_dedup_within_competitor():
    """Same heading repeated in one competitor should count as 1."""
    competitors = [
        _comp("https://c1.com", ["Features", "Features", "Features"]),
        _comp("https://c2.com", ["Pricing"]),
    ]
    missing = find_missing_topics([], competitors)
    topics = [m["topic"] for m in missing]
    # Each URL contributes the heading once; features only appears on 1 competitor
    assert "features" not in topics


def test_missing_topics_case_insensitive():
    your = ["PRICING GUIDE"]
    competitors = [
        _comp("https://c1.com", ["Pricing Guide", "Features"]),
        _comp("https://c2.com", ["pricing guide", "FAQ"]),
    ]
    missing = find_missing_topics(your, competitors)
    topics = [m["topic"] for m in missing]
    assert not any("pricing" in t for t in topics)


# ── find_paa_gaps ────────────────────────────────────────────────────────


def test_paa_gaps_unanswered():
    """PAA questions not covered in content should be flagged."""
    headings = ["Best SEO Tools"]
    text = "Here are the best seo tools for your business."
    questions = [
        "What is the average salary for an SEO specialist?",
        "How long does technical audit migration take?",
    ]
    gaps = find_paa_gaps(headings, text, questions)

    assert len(gaps) >= 1
    for g in gaps:
        assert g["kind"] == "paa"
        assert g["topic"] in questions


def test_paa_gaps_answered_in_heading():
    """PAA question matching a heading should NOT be flagged."""
    headings = ["What is the best free SEO tool?"]
    text = "some content"
    questions = ["What is the best free SEO tool?"]

    gaps = find_paa_gaps(headings, text, questions)
    assert len(gaps) == 0


def test_paa_gaps_answered_in_text():
    """PAA question with key terms present in text should NOT be flagged."""
    headings = []
    text = "our seo tools pricing plans start at $10 per month and cost varies by features"
    questions = ["How much do SEO tools cost?"]

    gaps = find_paa_gaps(headings, text, questions)
    assert len(gaps) == 0


def test_paa_gaps_empty():
    gaps = find_paa_gaps([], "", [])
    assert gaps == []


# ── find_serp_feature_opportunities ──────────────────────────────────────


def test_serp_opportunities_featured_snippet():
    serp = {
        "has_featured_snippet": True,
        "has_knowledge_panel": False,
        "has_video_carousel": False,
        "has_image_pack": False,
        "has_local_pack": False,
        "people_also_ask": [],
    }
    your_data = {"h2": ["Overview"], "h3": [], "has_schema": True}
    opps = find_serp_feature_opportunities(serp, your_data, [])

    assert any("featured snippet" in o["topic"].lower() for o in opps)
    for o in opps:
        assert o["kind"] == "serp_feature"


def test_serp_opportunities_video():
    serp = {
        "has_featured_snippet": False,
        "has_knowledge_panel": False,
        "has_video_carousel": True,
        "has_image_pack": False,
        "has_local_pack": False,
        "people_also_ask": [],
    }
    opps = find_serp_feature_opportunities(serp, None, [])
    assert any("video" in o["topic"].lower() for o in opps)


def test_serp_opportunities_schema_gap():
    serp = {
        "has_featured_snippet": False,
        "has_knowledge_panel": False,
        "has_video_carousel": False,
        "has_image_pack": False,
        "has_local_pack": False,
        "people_also_ask": [],
    }
    your_data = {"h2": [], "h3": [], "has_schema": False}
    competitors = [
        {"url": "https://a.com", "has_schema": True, "h2": [], "h3": []},
        {"url": "https://b.com", "has_schema": True, "h2": [], "h3": []},
        {"url": "https://c.com", "has_schema": False, "h2": [], "h3": []},
    ]
    opps = find_serp_feature_opportunities(serp, your_data, competitors)
    assert any("schema" in o["topic"].lower() for o in opps)


def test_serp_opportunities_none_when_clean():
    serp = {
        "has_featured_snippet": False,
        "has_knowledge_panel": False,
        "has_video_carousel": False,
        "has_image_pack": False,
        "has_local_pack": False,
        "people_also_ask": [],
    }
    your_data = {"h2": [], "h3": [], "has_schema": True}
    opps = find_serp_feature_opportunities(serp, your_data, [])
    assert len(opps) == 0


# ── find_content_gaps_node ───────────────────────────────────────────────


def test_content_gaps_node():
    """LangGraph node should populate missing_topics with richer objects."""
    state = {
        "target_domain": "https://mysite.com",
        "keywords": ["seo tools"],
        "results": [{
            "keyword": "seo tools",
            "your_url": "https://mysite.com/seo",
            "your_rank": 5,
            "your_page": 1,
            "top_competitors": [],
            "serp_features": {
                "has_featured_snippet": True,
                "has_knowledge_panel": False,
                "has_video_carousel": False,
                "has_image_pack": False,
                "has_local_pack": False,
                "people_also_ask": ["What is SEO?"],
            },
            "on_page_issues": [],
            "missing_topics": [],
            "backlink_gap": [],
            "internal_link_score": 0.0,
            "internal_link_issues": [],
            "page_speed": None,
            "your_page_data": None,
            "raw_competitor_data": [
                _comp("https://c1.com", ["Features", "Pricing", "Reviews"],
                      ["Ahrefs", "SEMrush"], has_schema=True),
                _comp("https://c2.com", ["Features", "Pricing", "Comparison"],
                      ["Moz", "SEMrush"], has_schema=True),
            ],
        }],
        "final_report": None,
        "errors": [],
    }

    new_state = find_content_gaps_node(state)
    topics = new_state["results"][0]["missing_topics"]
    topic_strings = [t["topic"] for t in topics]

    assert any("features" in t for t in topic_strings)
    assert any("pricing" in t for t in topic_strings)
    # PAA gap should be included
    assert any(t["kind"] == "paa" for t in topics)
    # SERP opportunities should be included
    assert any(t["kind"] == "serp_feature" for t in topics)
    assert len(new_state["errors"]) == 0


def test_content_gaps_node_handles_errors():
    """Errors should be caught per keyword."""
    state = {
        "target_domain": "https://mysite.com",
        "keywords": ["seo tools"],
        "results": [{
            "keyword": "seo tools",
            "your_url": None,
            "your_rank": None,
            "your_page": None,
            "top_competitors": [],
            "serp_features": "this will cause an error",
            "on_page_issues": [],
            "missing_topics": [],
            "backlink_gap": [],
            "internal_link_score": 0.0,
            "internal_link_issues": [],
            "page_speed": None,
            "your_page_data": None,
            "raw_competitor_data": "not a list",
        }],
        "final_report": None,
        "errors": [],
    }

    new_state = find_content_gaps_node(state)
    assert len(new_state["errors"]) == 1
    assert "find_content_gaps" in new_state["errors"][0]
