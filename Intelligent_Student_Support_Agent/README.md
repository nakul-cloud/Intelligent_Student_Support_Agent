# Intelligent Student Support Agent

Production-grade multi-turn conversational AI support system for university students featuring:
- Tool-calling agentic loop (OpenAI & Groq Llama 3.3 70B)
- Dual-tier memory (Redis fast cache + PostgreSQL durable storage)
- Retrieval-Augmented Generation (Qdrant vector store + OpenAI text-embedding-3-small)
- Complete PostgreSQL-tracked file ingestion lifecycle
- Dual observability (Local turn-by-turn JSON tracer + LangSmith dashboard)
- Enterprise FastAPI backend with routes, controllers, and services

## Getting Started

```bash
# 1. Start Docker containers (PostgreSQL, Redis, Qdrant)
just up

# 2. Initialize database & seed mock data
just db-init
just seed

# 3. Ingest student handbook into Qdrant
just ingest

# 4. Run application
just server     # Run FastAPI API on http://localhost:8000
just streamlit  # Run interactive testing interface
just cli        # Run terminal chat
```
