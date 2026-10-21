"""Agent execution tracing and observability module.

Exports:
- Tracer: Local turn-by-turn metrics capture, console renderer, and JSON persister.
- LangSmithAdapter: Decoupled adapter for optional remote LangSmith dashboard telemetry.
- langsmith_adapter: Singleton adapter instance.
"""

from tracing.langsmith_adapter import LangSmithAdapter, langsmith_adapter
from tracing.tracer import Tracer

__all__ = ["Tracer", "LangSmithAdapter", "langsmith_adapter"]
