# ⚙️ Configuration & Infrastructure (`app/config`)

The **Config Layer** manages application environment variables, asynchronous database connection pooling, Redis caching singletons, and domain constant enumerations.

---

## 🏗️ Configuration & Connection Architecture

```mermaid
flowchart TD
    Env[".env Configuration File / System Environment"] --> Settings["Pydantic BaseSettings (settings.py)<br/>• Type-safe parsing & validation<br/>• DB URLs, JWT secret, Groq keys, Fallback model"]

    Settings --> DB["PostgreSQL AsyncEngine (database.py)<br/>• pool_size=20, max_overflow=10<br/>• pool_pre_ping=True (stale recycling)<br/>• Zero SQLite Fallback Policy"]
    Settings --> Redis["Redis Async Client (redis.py)<br/>• Ephemeral L1 Sliding Window<br/>• Sliding-Window Rate Limiting<br/>• ping_redis() health verification"]
    Settings --> QdrantConfig["Qdrant Settings<br/>• qdrant_url & collection configuration"]

    DB --> SessionFactory["async_sessionmaker (AsyncSessionLocal)<br/>Yields AsyncSession via get_db dependency"]
```

---

## 📁 Module Inventory

| File | Core Component | Role & Functionality |
|---|---|---|
| [`settings.py`](./settings.py) | `Settings`, `settings` | Pydantic v2 settings class reading from `.env` (database URLs, JWT secrets, Groq API key, Qdrant host, embedding models). |
| [`database.py`](./database.py) | `engine`, `AsyncSessionLocal`, `get_db`, `init_db` | Asynchronous SQLAlchemy 2.0 PostgreSQL engine and session factory. Enforces pure PostgreSQL with zero SQLite fallback. |
| [`redis.py`](./redis.py) | `redis_client`, `ping_redis` | Async Redis client singleton for ephemeral conversation caching and health verification. |
| [`constants.py`](./constants.py) | Enumerations | Centralized enums: `FeeStatus`, `ScholarshipStatus`, `TicketPriority`, `TicketStatus`, `DocumentStatus`, `AppEnvironment`. |

---

## 💎 Zero-SQLite Architectural Invariant

- `app/config/database.py` binds exclusively to PostgreSQL (`settings.database_url`).
- If PostgreSQL is unreachable upon startup, `check_and_initialize_database()` immediately raises a `RuntimeError` with diagnostic instructions to start Docker containers (`just up`), eliminating silent fallback and database drift.
