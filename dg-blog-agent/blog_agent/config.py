"""Configuration loaded from environment variables.

Two MongoDB databases are involved (kept deliberately separate):

* ``MONGO_URI``      — source/web-app DB, READ-ONLY: ``articles`` + ``documents``.
* ``APP_MONGO_URI``  — our system DB ("Mongo B"), READ/WRITE: ``blog_suggestions``.

The LLM provider + model + key are generic so the same graph runs against
anthropic / openai / gemini just by changing env.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All settings for the Blog Improver agent, loaded from ``.env``."""

    # --- LLM provider (from env) ------------------------------------------
    # One of: anthropic | openai | gemini
    llm_provider: str = "gemini"
    # Generic model id; falls back to a per-provider default when blank.
    llm_model: str = ""

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

    # --- MongoDB (from env) -----------------------------------------------
    # Mongo A (source, read-only): articles + documents.
    mongo_uri: str = ""
    # Mongo B (system, read/write): blog_suggestions.
    app_mongo_uri: str = ""

    # --- Code defaults (rarely changed; override via env only if needed) ---
    llm_temperature: float = Field(default=0.3, ge=0.0, le=2.0)

    articles_collection: str = "articles"
    documents_collection: str = "documents"
    suggestions_collection: str = "blog_suggestions"

    # Which article types count as "blogs".
    article_types: list[str] = ["Blog"]
    # Hard safety ceiling — the run can never analyse more than this.
    max_blogs_per_run: int = Field(default=100, ge=1)
    # Public site base; blog url = <base>/blog/<slug>.
    site_base_url: str = "https://www.designgurus.io"

    # --- Workflow parameter defaults (also passable as graph/CLI params) ---
    # x: only review blogs not updated in at least this many months.
    months_old: int = Field(default=6, ge=1, le=60)
    # n: max blogs to pull per run.
    blog_limit: int = Field(default=5, ge=1, le=500)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
