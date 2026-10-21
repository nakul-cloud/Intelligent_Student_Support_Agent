"""Agent execution package.

Exports:
- run_agent: Multi-turn Reasoning-Action agent loop.
- groq_client: Synchronous OpenAI-compatible Groq client.
- async_groq_client: Asynchronous OpenAI-compatible Groq client.
- get_groq_client / get_async_groq_client: Client accessors.
"""

from app.agent.agent_loop import run_agent
from app.agent.client import (
    async_groq_client,
    get_async_groq_client,
    get_groq_client,
    groq_client,
)

__all__ = [
    "run_agent",
    "groq_client",
    "async_groq_client",
    "get_groq_client",
    "get_async_groq_client",
]
