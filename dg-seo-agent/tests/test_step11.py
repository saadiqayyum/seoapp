"""Test Step 11: graph.py — LangGraph pipeline wiring.

Tests the full pipeline with mocked tool nodes to verify data flows correctly.
"""

from unittest.mock import patch

from seo_agent.graph import build_graph
from seo_agent.state import SEOAgentState


# ── Mock node functions ──────────────────────────────────────────────────
# Each mock simulates what the real node does: reads state, adds data, returns state.

def mock_check_rankings(state: dict) -> dict:
    results = []
    for keyword in state["keywords"]:
        results.append({
            "keyword": keyword,
            "your_url": f"https://mysite.com/{keyword.replace(' ', '-')}",
            "your_rank": 8,
            "your_page": 1,
            "top_competitors": [
                {"rank": 1, "url": "https://comp1.com/page", "title": "Comp 1", "domain": "comp1.com"},
                {"rank": 2, "url": "https://comp2.com/page", "title": "Comp 2", "domain": "comp2.com"},
            ],
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
            "raw_competitor_data": [],
        })
    return {**state, "results": results}


def mock_analyse_competitors(state: dict) -> dict:
    for kw in state["results"]:
        kw["raw_competitor_data"] = [
            {"url": "https://comp1.com/page", "title": "Comp 1", "meta_description": "",
             "h1": ["Comp 1"], "h2": ["Features", "Pricing"], "h3": [],
             "word_count": 2000, "has_schema": True, "internal_links": 10, "external_links": 5},
            {"url": "https://comp2.com/page", "title": "Comp 2", "meta_description": "",
             "h1": ["Comp 2"], "h2": ["Features", "Reviews"], "h3": [],
             "word_count": 1800, "has_schema": False, "internal_links": 8, "external_links": 3},
        ]
    return state


def mock_audit_onpage(state: dict) -> dict:
    for kw in state["results"]:
        kw["on_page_issues"] = ["Title tag is 38 characters — too short (aim for 50-60)"]
    return state


def mock_pagespeed(state: dict) -> dict:
    for kw in state["results"]:
        kw["page_speed"] = {"score": 72, "lcp": 3.2, "cls": 0.05}
        kw["on_page_issues"].append("Performance score is 72/100 — room for improvement")
    return state


def mock_find_backlink_gaps(state: dict) -> dict:
    for kw in state["results"]:
        kw["backlink_gap"] = ["bigpub.com (DA: 85, links to 2 competitors)"]
    return state


def mock_find_content_gaps(state: dict) -> dict:
    for kw in state["results"]:
        kw["missing_topics"] = ["features", "reviews", "[PAA] What is SEO?"]
    return state


def mock_audit_internal_links(state: dict) -> dict:
    for kw in state["results"]:
        kw["internal_link_score"] = 0.45
        kw["internal_link_issues"] = ["Only 2 internal links point to this page"]
    return state


# ── Tests ────────────────────────────────────────────────────────────────


def test_build_graph_compiles():
    """Graph should compile without errors."""
    graph = build_graph()
    assert graph is not None


def test_graph_node_order():
    """Graph should contain every pipeline node."""
    graph = build_graph()
    node_names = list(graph.get_graph().nodes.keys())
    pipeline_nodes = [n for n in node_names if not n.startswith("__")]

    expected = {
        "check_rankings",
        "analyse_competitors",
        "audit_onpage",
        "pagespeed",
        "find_content_gaps",
        "competitor_insights",
        "audit_internal_links",
    }
    assert expected.issubset(set(pipeline_nodes))


def test_full_pipeline_with_mocks():
    """Full pipeline should flow data through all nodes correctly."""
    with patch("seo_agent.graph.check_rankings_node", side_effect=mock_check_rankings), \
         patch("seo_agent.graph.analyse_competitors_node", side_effect=mock_analyse_competitors), \
         patch("seo_agent.graph.audit_onpage_node", side_effect=mock_audit_onpage), \
         patch("seo_agent.graph.get_pagespeed", return_value={"score": 72, "lcp": 3.2}), \
         patch("seo_agent.graph.format_pagespeed_issues", return_value=["Score is 72/100"]), \
         patch("seo_agent.graph.find_content_gaps_node", side_effect=mock_find_content_gaps), \
         patch("seo_agent.graph.competitor_insights_node", side_effect=lambda s: s), \
         patch("seo_agent.graph.audit_internal_links_node", side_effect=mock_audit_internal_links):

        graph = build_graph()
        initial_state: SEOAgentState = {
            "target_domain": "https://mysite.com",
            "keywords": ["seo tools", "keyword research"],
            "results": [],
            "final_report": None,
            "errors": [],
        }

        final_state = graph.invoke(initial_state)

    # Should have results for both keywords
    assert len(final_state["results"]) == 2

    kw1 = final_state["results"][0]
    assert kw1["keyword"] == "seo tools"
    assert kw1["your_rank"] == 8
    assert len(kw1["raw_competitor_data"]) == 2
    assert len(kw1["on_page_issues"]) >= 1
    assert kw1["page_speed"] is not None
    assert len(kw1["missing_topics"]) >= 1
    assert kw1["internal_link_score"] == 0.45
    assert len(kw1["internal_link_issues"]) >= 1

    kw2 = final_state["results"][1]
    assert kw2["keyword"] == "keyword research"


def test_pipeline_single_keyword():
    """Pipeline should work fine with just one keyword."""
    with patch("seo_agent.graph.check_rankings_node", side_effect=mock_check_rankings), \
         patch("seo_agent.graph.analyse_competitors_node", side_effect=mock_analyse_competitors), \
         patch("seo_agent.graph.audit_onpage_node", side_effect=mock_audit_onpage), \
         patch("seo_agent.graph.get_pagespeed", return_value=None), \
         patch("seo_agent.graph.format_pagespeed_issues", return_value=["N/A"]), \
         patch("seo_agent.graph.find_content_gaps_node", side_effect=mock_find_content_gaps), \
         patch("seo_agent.graph.competitor_insights_node", side_effect=lambda s: s), \
         patch("seo_agent.graph.audit_internal_links_node", side_effect=mock_audit_internal_links):

        graph = build_graph()
        final_state = graph.invoke({
            "target_domain": "https://mysite.com",
            "keywords": ["seo tools"],
            "results": [],
            "final_report": None,
            "errors": [],
        })

    assert len(final_state["results"]) == 1
    assert final_state["results"][0]["keyword"] == "seo tools"


def test_pipeline_preserves_errors():
    """Errors from earlier nodes should persist through the pipeline."""

    def rankings_with_error(state):
        result = mock_check_rankings(state)
        result["errors"] = ["[check_rankings] keyword='bad' error: timeout"]
        return result

    with patch("seo_agent.graph.check_rankings_node", side_effect=rankings_with_error), \
         patch("seo_agent.graph.analyse_competitors_node", side_effect=mock_analyse_competitors), \
         patch("seo_agent.graph.audit_onpage_node", side_effect=mock_audit_onpage), \
         patch("seo_agent.graph.get_pagespeed", return_value=None), \
         patch("seo_agent.graph.format_pagespeed_issues", return_value=[]), \
         patch("seo_agent.graph.find_content_gaps_node", side_effect=mock_find_content_gaps), \
         patch("seo_agent.graph.competitor_insights_node", side_effect=lambda s: s), \
         patch("seo_agent.graph.audit_internal_links_node", side_effect=mock_audit_internal_links):

        graph = build_graph()
        final_state = graph.invoke({
            "target_domain": "https://mysite.com",
            "keywords": ["seo tools"],
            "results": [],
            "final_report": None,
            "errors": [],
        })

    # Error from check_rankings should still be present
    assert len(final_state["errors"]) >= 1
    assert "check_rankings" in final_state["errors"][0]
