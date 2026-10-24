"""Groq LLM Provider.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for building, configuring,
  and caching Groq-compatible LLM client instances from settings.
- Open/Closed (OCP): Closed for modification; observability is applied via the
  external LangSmithAdapter decorator without modifying client factory code.
"""

from openai import AsyncOpenAI, OpenAI
from app.config.settings import settings
from app.utils.logger import logger
from tracing.langsmith_adapter import langsmith_adapter


class GroqProvider:
    """Single Responsibility: Builds and provides configured Groq model clients."""

    _sync_client: OpenAI | None = None
    _async_client: AsyncOpenAI | None = None

    @classmethod
    def _get_api_key(cls) -> str:
        """Safely retrieve the Groq API key from settings."""
        key = settings.groq_api_key.strip()
        if not key or "your_groq_api_key" in key:
            logger.warning(
                "GroqProvider: GROQ_API_KEY is not set or using placeholder in .env. "
                "Inference calls will require a valid Groq API key."
            )
            return "unconfigured_key"
        return key

    @classmethod
    def get_client(cls) -> OpenAI:
        """Return cached synchronous Groq client singleton wrapped with optional telemetry."""
        if cls._sync_client is None:
            raw = OpenAI(
                api_key=cls._get_api_key(),
                base_url=settings.groq_base_url,
                timeout=30.0,
                max_retries=2,
            )
            cls._sync_client = langsmith_adapter.wrap_client(raw)
        return cls._sync_client

    @classmethod
    def get_async_client(cls) -> AsyncOpenAI:
        """Return cached asynchronous Groq client singleton wrapped with optional telemetry."""
        if cls._async_client is None:
            raw = AsyncOpenAI(
                api_key=cls._get_api_key(),
                base_url=settings.groq_base_url,
                timeout=30.0,
                max_retries=2,
            )
            cls._async_client = langsmith_adapter.wrap_client(raw)
        return cls._async_client
