"""Groq LLM Client Provider.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for instantiating and configuring
  the Groq-compatible LLM client instances from settings.
- Open/Closed (OCP): Closed for modification; observability is applied via the
  external LangSmithAdapter decorator without modifying client factory code.
- Dependency Inversion (DIP): Exposes standard OpenAI and AsyncOpenAI interfaces
  for consumer agent loops and services.
"""

from openai import AsyncOpenAI, OpenAI
from app.config.settings import settings
from app.utils.logger import logger
from tracing.langsmith_adapter import langsmith_adapter


def _get_configured_api_key() -> str:
    """Safely retrieve the Groq API key from settings.

    Returns the stripped API key or a fallback string to prevent immediate
    module-level instantiation exceptions when keys have not yet been provided.
    """
    key = settings.groq_api_key.strip()
    if not key or "your_groq_api_key" in key:
        logger.warning(
            "Client: GROQ_API_KEY is not set or using placeholder in .env. "
            "Inference calls will require a valid Groq API key."
        )
        return "unconfigured_key"
    return key


# ==============================================================================
# Base Client Instantiation (Pure Groq / OpenAI Wire Protocol)
# ==============================================================================

_raw_sync_client: OpenAI = OpenAI(
    api_key=_get_configured_api_key(),
    base_url=settings.groq_base_url,
)

_raw_async_client: AsyncOpenAI = AsyncOpenAI(
    api_key=_get_configured_api_key(),
    base_url=settings.groq_base_url,
)

# ==============================================================================
# Decorated Client Singletons (Optional LangSmith Telemetry via Adapter)
# Returns clients unmodified if ENABLE_LANGSMITH=false in configuration.
# ==============================================================================

groq_client: OpenAI = langsmith_adapter.wrap_client(_raw_sync_client)
async_groq_client: AsyncOpenAI = langsmith_adapter.wrap_client(_raw_async_client)


def get_groq_client() -> OpenAI:
    """Return the configured synchronous Groq client singleton."""
    return groq_client


def get_async_groq_client() -> AsyncOpenAI:
    """Return the configured asynchronous Groq client singleton."""
    return async_groq_client
