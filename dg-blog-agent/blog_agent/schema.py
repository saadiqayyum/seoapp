"""Structured contracts for the Blog Improver.

``BlogAnalysis`` is the schema the LLM MUST return. It is stored verbatim on the
suggestion document, so the field *aliases* are camelCase to stay byte-compatible
with the existing ``blog_suggestions`` shape produced by the original agent
(``overallScore``, ``proposedContent``, …). Python code uses the snake_case
attribute names; persistence dumps ``by_alias=True``.
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypedDict

ISSUE_CATEGORIES = (
    "seo",
    "clarity",
    "accuracy",
    "structure",
    "outdated",
    "grammar",
    "engagement",
)

SEVERITIES = ("low", "medium", "high")

RECOMMENDED_ACTIONS = ("no_change", "minor_edit", "major_rewrite")

IssueCategory = Literal[
    "seo", "clarity", "accuracy", "structure", "outdated", "grammar", "engagement"
]
Severity = Literal["low", "medium", "high"]
RecommendedAction = Literal["no_change", "minor_edit", "major_rewrite"]


class BlogIssue(BaseModel):
    """A single concrete issue found in the blog."""

    category: IssueCategory
    severity: Severity
    location: str = Field(
        description="Where in the blog the issue occurs (section/heading/quote)."
    )
    problem: str = Field(description="What is wrong.")
    suggestion: str = Field(description="Concrete, actionable fix.")


class BlogAnalysis(BaseModel):
    """The structured analysis the LLM returns — never parsed from free text."""

    model_config = ConfigDict(populate_by_name=True)

    overall_score: int = Field(
        alias="overallScore",
        ge=1,
        le=10,
        description="Overall quality, 1 (poor) to 10 (excellent).",
    )
    summary: str = Field(description="Short overall assessment of the blog.")
    change_summary: str = Field(
        alias="changeSummary",
        description=(
            "A concise, human-readable summary of the concrete changes made in "
            "proposedContent versus the original (what was added, rewritten, fixed)."
        ),
    )
    recommended_action: RecommendedAction = Field(alias="recommendedAction")
    issues: list[BlogIssue] = Field(
        default_factory=list,
        description="Specific issues found, most important first.",
    )
    proposed_content: str = Field(
        alias="proposedContent",
        description=(
            "The actual improved blog body in Markdown — the rewritten/edited content "
            "itself, ready to review and publish. NOT instructions about what to change. "
            "Reproduce the full body with the improvements applied. Empty string only if "
            "recommendedAction is no_change."
        ),
    )
    proposed_title: Optional[str] = Field(
        default=None,
        alias="proposedTitle",
        description="Improved title, only if it should change.",
    )
    proposed_seo_title: Optional[str] = Field(default=None, alias="proposedSeoTitle")
    proposed_seo_description: Optional[str] = Field(
        default=None, alias="proposedSeoDescription"
    )


class BlogRef(TypedDict, total=False):
    """Agent-facing reference to one published blog (single source of truth)."""

    article_id: str
    slug: str
    title: str
    sub_title: Optional[str]
    tags: list[str]
    article_type: str
    seo_title: Optional[str]
    seo_description: Optional[str]
    document_id: Optional[str]
    updated_at: Optional[str]
    url: str


class AnalyzeResult(TypedDict, total=False):
    """Per-blog outcome captured into ``results`` (failures never abort the run)."""

    article_id: str
    slug: str
    ok: bool
    suggestion_id: Optional[str]
    error: Optional[str]
