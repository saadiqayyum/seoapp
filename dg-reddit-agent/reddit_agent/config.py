"""Configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """All settings for the Reddit Agent, loaded from .env file."""

    # Discovery (Google via SerpAPI)
    serpapi_key: str = ""

    # LLM (Gemini)
    google_api_key: str = ""
    gemini_model_id: str = "gemini-2.0-flash"

    # Reddit thread fetching
    reddit_user_agent: str = "dg-agents:reddit-agent:v1 (by /u/dg-agents)"
    reddit_bearer_token: str = ""

    # Tuning
    max_threads_per_keyword: int = Field(default=10, ge=1, le=50)
    max_comments_per_thread: int = Field(default=10, ge=0, le=50)
    cache_ttl_hours: int = Field(default=24, ge=1)

    # Infrastructure (parity with seo-agent cache manager)
    redis_url: str = "redis://localhost:6379"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
