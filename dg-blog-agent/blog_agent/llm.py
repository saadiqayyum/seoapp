"""Provider-agnostic LLM access via LangChain's ``init_chat_model``.

The provider/model/key come from env (``LLM_PROVIDER`` / ``LLM_MODEL`` / the
provider's key). ``init_chat_model`` is LangChain's standard multi-provider
entry point; structured output uses the model's native ``with_structured_output``
so the result is validated, never parsed from text.
"""

import logging

from langchain.chat_models import init_chat_model

from blog_agent.config import settings
from blog_agent.schema import BlogAnalysis

logger = logging.getLogger(__name__)

# Map our env provider name -> LangChain ``model_provider`` + default model + key attr.
_PROVIDERS = {
    "anthropic": ("anthropic", "claude-opus-4-8", "anthropic_api_key"),
    "openai": ("openai", "gpt-4.1", "openai_api_key"),
    "gemini": ("google_genai", "gemini-2.5-flash", "google_api_key"),
}


def get_chat_model():
    """Build the configured chat model through ``init_chat_model``."""
    provider = (settings.llm_provider or "gemini").lower()
    if provider not in _PROVIDERS:
        raise RuntimeError(
            f'Unknown LLM_PROVIDER "{provider}". Use one of: {", ".join(_PROVIDERS)}.'
        )
    lc_provider, default_model, key_attr = _PROVIDERS[provider]
    model = settings.llm_model or default_model
    api_key = getattr(settings, key_attr, "")
    if not api_key:
        raise RuntimeError(
            f'No API key for provider "{provider}". Set {key_attr.upper()} in .env.'
        )

    logger.info("Using LLM %s:%s", lc_provider, model)
    return init_chat_model(
        model,
        model_provider=lc_provider,
        api_key=api_key,
        temperature=settings.llm_temperature,
    )


def get_structured_model():
    """Chat model bound to the ``BlogAnalysis`` schema (validated output)."""
    return get_chat_model().with_structured_output(BlogAnalysis)
