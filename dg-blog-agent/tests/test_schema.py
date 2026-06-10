from blog_agent.schema import BlogAnalysis


def test_camelcase_aliases_roundtrip():
    analysis = BlogAnalysis.model_validate(
        {
            "overallScore": 7,
            "summary": "Decent but thin.",
            "changeSummary": "Expanded intro; fixed headings.",
            "recommendedAction": "minor_edit",
            "issues": [
                {
                    "category": "seo",
                    "severity": "medium",
                    "location": "H1",
                    "problem": "No target keyword.",
                    "suggestion": "Add keyword to H1.",
                }
            ],
            "proposedContent": "# Title\n\nBody.",
        }
    )
    assert analysis.overall_score == 7
    assert analysis.recommended_action == "minor_edit"

    # Persisted form must stay camelCase (compatible with the suggestion contract).
    dumped = analysis.model_dump(by_alias=True)
    assert dumped["overallScore"] == 7
    assert dumped["changeSummary"].startswith("Expanded")
    assert dumped["proposedContent"].startswith("# Title")
    assert dumped["proposedTitle"] is None
