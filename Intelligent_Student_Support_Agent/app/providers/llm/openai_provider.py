"""OpenAI LLM Provider.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for building and configuring
  OpenAI model client instances.
"""

from openai import AsyncOpenAI, OpenAI
from app.config.settings import settings
from tracing.langsmith_adapter import langsmith_adapter


class OpenAIProvider:
    """Single Responsibility: Builds and provides configured OpenAI model clients."""

    _sync_client: OpenAI | None = None
    _async_client: AsyncOpenAI | None = None

    @classmethod
    def get_client(cls) -> OpenAI:
        """Return cached synchronous OpenAI client singleton."""
        if cls._sync_client is None:
            raw = OpenAI(
                api_key=settings.openai_api_key or "unconfigured_key",
                timeout=30.0,
                max_retries=2,
            )
            cls._sync_client = langsmith_adapter.wrap_client(raw)
        return cls._sync_client

    @classmethod
    def get_async_client(cls) -> AsyncOpenAI:
        """Return cached asynchronous OpenAI client singleton."""
        if cls._async_client is None:
            raw = AsyncOpenAI(
                api_key=settings.openai_api_key or "unconfigured_key",
                timeout=30.0,
                max_retries=2,
            )
            cls._async_client = langsmith_adapter.wrap_client(raw)
        return cls._async_client
