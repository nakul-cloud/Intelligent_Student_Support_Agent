"""LangSmith Telemetry Adapter.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for adapting and decorating
  OpenAI-compatible clients with remote LangSmith telemetry when enabled.
- Open/Closed (OCP): Closed for modification; remote tracing is enabled or disabled
  entirely through application settings without altering core client code.
- Liskov Substitution (LSP): The returned client is guaranteed to have the exact same
  interface as the underlying client, allowing callers to use it interchangeably.
- Dependency Inversion (DIP): Injects application settings and acts as an external
  adapter, keeping core agent and client modules completely free of vendor lock-in.
"""

import os
from typing import Any, TypeVar
from openai import AsyncOpenAI, OpenAI
from app.config.settings import Settings, settings
from app.utils.logger import logger

ClientType = TypeVar("ClientType", OpenAI, AsyncOpenAI)


class LangSmithAdapter:
    """Adapter for configuring and applying optional LangSmith telemetry to LLM clients."""

    def __init__(self, app_settings: Settings = settings) -> None:
        """Initialize adapter with application configuration settings."""
        self._settings = app_settings
        self._is_configured: bool = False

    def is_enabled(self) -> bool:
        """Check if LangSmith tracing is enabled and configured with a valid API key."""
        if not self._settings.enable_langsmith:
            return False

        api_key = self._settings.langsmith_api_key.strip()
        if not api_key or "your_langsmith_api_key" in api_key:
            return False

        return True

    def configure_environment(self) -> bool:
        """Configure LangSmith environment variables if enabled in settings."""
        if self._is_configured:
            return True

        if not self.is_enabled():
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            logger.debug("LangSmithAdapter: Remote LangSmith tracing is disabled.")
            return False

        api_key = self._settings.langsmith_api_key.strip()
        project = self._settings.langsmith_project.strip() or "student-support-agent"

        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = project

        self._is_configured = True
        logger.info(f"LangSmithAdapter: Activated remote observability for project '{project}'.")
        return True

    def wrap_client(self, client: ClientType) -> ClientType:
        """Decorate an OpenAI or AsyncOpenAI client with LangSmith telemetry if enabled.

        If LangSmith is disabled or unavailable, returns the client unmodified.

        Args:
            client: The raw OpenAI or AsyncOpenAI client instance.

        Returns:
            The wrapped client (or original client if tracing is disabled).
        """
        if not self.is_enabled():
            return client

        try:
            self.configure_environment()
            from langsmith.wrappers import wrap_openai

            wrapped = wrap_openai(client)
            logger.info("LangSmithAdapter: Successfully decorated client with LangSmith tracing.")
            return wrapped
        except Exception as exc:
            logger.warning(
                f"LangSmithAdapter: Failed to wrap client with LangSmith ({exc}). "
                "Falling back to unmodified raw client."
            )
            return client

    def set_run_metadata(self, **kwargs: Any) -> dict[str, Any]:
        """Attach run-level metadata tags to telemetry traces."""
        metadata = {k: v for k, v in kwargs.items() if v is not None}
        logger.debug(f"LangSmithAdapter: Run metadata attached: {metadata}")
        return metadata


# Singleton adapter instance initialized with application settings
langsmith_adapter = LangSmithAdapter()
