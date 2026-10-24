"""Groq LLM Client Provider.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for exposing configured
  Groq-compatible LLM client instances from LLMFactory and GroqProvider.
- Open/Closed (OCP): Closed for modification; provider selection and fallback mechanisms
  are governed by LLMFactory without modifying consumer contracts.
- Dependency Inversion (DIP): Exposes standard OpenAI and AsyncOpenAI interfaces
  for consumer agent loops and services.
"""

from openai import AsyncOpenAI, OpenAI
from app.providers.llm.factory import LLMFactory
from app.providers.llm.groq_provider import GroqProvider

# Singleton instances provisioned via LLMFactory with dynamic fallback capability
groq_client: OpenAI = LLMFactory.get_groq_client()
async_groq_client: AsyncOpenAI = LLMFactory.get_fallback_enabled_async_client()


def get_groq_client() -> OpenAI:
    """Return the configured synchronous Groq client singleton."""
    return groq_client


def get_async_groq_client() -> AsyncOpenAI:
    """Return the configured asynchronous Groq client singleton."""
    return async_groq_client


__all__ = [
    "groq_client",
    "async_groq_client",
    "get_groq_client",
    "get_async_groq_client",
    "GroqProvider",
    "LLMFactory",
]
