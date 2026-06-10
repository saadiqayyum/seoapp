from blog_agent.tools.blog_content import extract_document_content


def test_empty_document():
    assert extract_document_content(None) == ("", [])
    assert extract_document_content({}) == ("", [])


def test_flat_sections_and_outline():
    latest = {
        "sections": [
            {"sectionType": "markdown", "markdown": {"text": "Intro para."}},
            {"sectionType": "markdown", "markdown": {"text": "Second para."}},
        ],
        "outline": [{"title": "Intro", "type": "H2"}, {"title": "Body", "type": "H2"}],
    }
    text, outline = extract_document_content(latest)
    assert text == "Intro para.\n\nSecond para."
    assert outline == ["Intro", "Body"]


def test_nested_sections():
    latest = {
        "sections": [
            {
                "sectionType": "collapse",
                "sections": [
                    {"markdown": {"text": "Nested A"}},
                    {"markdown": {"text": "Nested B"}},
                ],
            }
        ]
    }
    text, outline = extract_document_content(latest)
    assert text == "Nested A\n\nNested B"
    assert outline == []


def test_unknown_shapes_skipped():
    latest = {"sections": [{"sectionType": "image", "src": "x.png"}, "garbage"]}
    text, outline = extract_document_content(latest)
    assert text == ""
    assert outline == []
