"""Centralized LLM Factory with Dynamic Groq Fallback Support.

Patterned after standard enterprise multi-provider LLM architectures:
- Single Responsibility (SRP): Exclusively governs model resolution, client provisioning,
  and dynamic fallback orchestration.
- Open/Closed (OCP): New model providers or fallback chains can be introduced
  without modifying consumer agent loops.
- Dependency Inversion (DIP): Consumer modules invoke standard interfaces rather
  than coupling directly to provider wire implementations.
"""

from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI, OpenAI

from app.config.settings import settings
from app.providers.llm.groq_provider import GroqProvider
from app.providers.llm.openai_provider import OpenAIProvider
from app.utils.logger import logger


class FallbackChatCompletionsProxy:
    """Proxy around AsyncOpenAI.chat.completions that dynamically retries with fallback model."""

    def __init__(self, raw_completions: Any, fallback_model: str):
        self._raw = raw_completions
        self.fallback_model = fallback_model

    async def create(self, **kwargs: Any) -> Any:
        primary_model = kwargs.get("model", settings.groq_model)
        fallback = kwargs.pop("fallback_model", self.fallback_model)

        try:
            return await self._raw.create(**kwargs)
        except Exception as primary_exc:
            if not fallback or primary_model == fallback:
                raise primary_exc

            logger.warning(
                f"LLMFactory: Primary model '{primary_model}' failed ({type(primary_exc).__name__}: {primary_exc}). "
                f"Switching dynamically to fallback model '{fallback}'..."
            )
            fallback_kwargs = dict(kwargs)
            fallback_kwargs["model"] = fallback
            try:
                return await self._raw.create(**fallback_kwargs)
            except Exception as fallback_exc:
                logger.error(
                    f"LLMFactory: Fallback model '{fallback}' also failed ({type(fallback_exc).__name__}: {fallback_exc}). "
                    f"Both primary ('{primary_model}') and fallback ('{fallback}') exhausted."
                )
                raise fallback_exc from primary_exc

    def __getattr__(self, name: str) -> Any:
        return getattr(self._raw, name)


class FallbackAsyncClientProxy:
    """Proxy around AsyncOpenAI that provides fallback-enabled chat completions."""

    def __init__(self, raw_client: AsyncOpenAI, fallback_model: str):
        self._raw_client = raw_client
        self.fallback_model = fallback_model
        self.chat = type("ChatProxy", (), {})()
        self.chat.completions = FallbackChatCompletionsProxy(
            raw_client.chat.completions,
            fallback_model=fallback_model,
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._raw_client, name)


class LLMFactory:
    """Centralized LLM Factory providing primary model providers with automatic dynamic fallbacks.

    Default Model Configuration (Dynamic via Settings / .env):
      - Primary Model  : settings.groq_model (e.g. 'openai/gpt-oss-120b')
      - Fallback Model : settings.groq_fallback_model (e.g. 'qwen/qwen3.8-27b')
    """

    @classmethod
    def get_primary_model(cls) -> str:
        """Returns the primary Groq chat model name configured in settings."""
        return settings.groq_model

    @classmethod
    def get_fallback_model(cls) -> str:
        """Returns the dynamic fallback model name configured in settings."""
        return settings.groq_fallback_model

    @classmethod
    def get_groq_client(cls) -> OpenAI:
        """Returns the configured synchronous Groq client singleton."""
        return GroqProvider.get_client()

    @classmethod
    def get_async_groq_client(cls) -> AsyncOpenAI:
        """Returns the configured asynchronous Groq client singleton."""
        return GroqProvider.get_async_client()

    @classmethod
    def get_fallback_enabled_async_client(cls) -> AsyncOpenAI:
        """Returns an asynchronous Groq client with built-in transparent dynamic fallback."""
        raw_client = GroqProvider.get_async_client()
        return FallbackAsyncClientProxy(
            raw_client=raw_client,
            fallback_model=cls.get_fallback_model(),
        )  # type: ignore[return-value]

    @classmethod
    def get_openai_client(cls) -> OpenAI:
        """Returns the configured synchronous OpenAI client singleton."""
        return OpenAIProvider.get_client()

    @classmethod
    def get_async_openai_client(cls) -> AsyncOpenAI:
        """Returns the configured asynchronous OpenAI client singleton."""
        return OpenAIProvider.get_async_client()

    @classmethod
    async def create_completion_with_fallback(
        cls,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        client: Optional[AsyncOpenAI] = None,
    ) -> Any:
        """Executes LLM chat completion with dynamic fallback on primary failure.

        Args:
            messages: Conversation message sequence.
            tools: OpenAI-compatible function calling schemas.
            temperature: Sampling temperature (defaults to settings.agent_temperature).
            model: Primary model override (defaults to settings.groq_model).
            fallback_model: Fallback model override (defaults to settings.groq_fallback_model).
            client: Async client override (defaults to GroqProvider.get_async_client()).

        Returns:
            ChatCompletion response object from primary or fallback model.
        """
        primary = model or cls.get_primary_model()
        fallback = fallback_model or cls.get_fallback_model()
        target_client = client or GroqProvider.get_async_client()
        temp = temperature if temperature is not None else settings.agent_temperature

        kwargs: Dict[str, Any] = {
            "messages": messages,
            "temperature": temp,
        }
        if tools:
            kwargs["tools"] = tools

        try:
            logger.info(f"LLMFactory: Executing turn completion using primary model '{primary}'...")
            return await target_client.chat.completions.create(model=primary, **kwargs)
        except Exception as primary_exc:
            if not fallback or primary == fallback:
                raise primary_exc

            logger.warning(
                f"LLMFactory: Primary model '{primary}' failed ({type(primary_exc).__name__}: {primary_exc}). "
                f"Triggering dynamic fallback to '{fallback}'..."
            )
            try:
                fallback_kwargs = dict(kwargs)
                fallback_kwargs["model"] = fallback
                return await target_client.chat.completions.create(**fallback_kwargs)
            except Exception as fallback_exc:
                logger.error(
                    f"LLMFactory: Dynamic fallback model '{fallback}' also failed ({type(fallback_exc).__name__}: {fallback_exc}). "
                    f"Both primary ('{primary}') and fallback ('{fallback}') exhausted."
                )
                raise fallback_exc from primary_exc
