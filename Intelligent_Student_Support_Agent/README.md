# Engineering & Implementation Guide 🛠️

> **Backend Service Documentation: Intelligent Student Support Agent**  
> This document details the technical implementation, internal module architecture, database models, testing personas, and API contracts for developers and evaluators working on or reviewing the backend codebase.

---

## 📑 Contents
1. [Backend Design Philosophy](#-backend-design-philosophy)
2. [Module Directory Anatomy](#-module-directory-anatomy)
3. [Seeded Test Student Personas](#-seeded-test-student-personas)
4. [Dual-Tier Memory Mechanics](#-dual-tier-memory-mechanics)
5. [API Endpoint Contracts](#-api-endpoint-contracts)
6. [Environment Variables Reference](#-environment-variables-reference)
7. [Developer Automation (`Justfile`)](#-developer-automation-justfile)

---

## 🏛️ Backend Design Philosophy

The backend is built following enterprise clean architecture and SOLID principles:
- **Separation of Concerns**: HTTP transport (`routes/`), request orchestration (`controllers/`), business domain logic (`services/`), agentic intelligence (`agent/`), and persistence (`models/`, `ai/retrieval/`).
- **Framework Independence**: The agent loop is a **raw, deterministic `while True` tool-calling loop** interacting directly with OpenAI / Groq APIs—avoiding rigid LangChain execution abstractions.
- **Privacy & Zero Cost**: 1536-dimensional embeddings run locally via `Orange/orange-nomic-v1.5-1536`, incurring **$0 in API embedding fees**.
- **Idempotent Ingestion**: Ingesting or updating documents safely clears previous vector points before upserting, preventing zombie chunks.

---

## 📂 Module Directory Anatomy

```text
Intelligent_Student_Support_Agent/
├── app/
│   ├── agent/                 # Agent loop execution & LLM client initialization
│   │   ├── agent_loop.py      # Core while True multi-turn tool calling loop
│   │   └── client.py          # Groq / OpenAI SDK wrapper with fallback support
│   ├── ai/
│   │   ├── ingestion/         # Document parsing, chunking, and embedding
│   │   │   ├── pdf_parser.py  # StructureAwarePDFParser (numbered sections & annexures)
│   │   │   ├── chunker.py     # SectionAwareChunker (dynamic tokens & sentence preservation)
│   │   │   └── embedder.py    # LocalEmbedder (Orange/orange-nomic-v1.5-1536)
│   │   └── retrieval/         # Vector database interactions
│   │       └── vector_store.py# QdrantVectorStore with payload indexing & metadata filters
│   ├── config/                # Central application configuration
│   │   ├── settings.py        # Pydantic BaseSettings loading from .env
│   │   ├── database.py        # Async SQLAlchemy engine & AsyncSessionLocal
│   │   ├── redis.py           # Async Redis connection pool & health checks
│   │   └── constants.py       # Domain StrEnums (FeeStatus, TicketStatus, DocumentStatus)
│   ├── controllers/           # HTTP Controller layer
│   │   └── ingestion_controller.py # File upload & status inspection handling
│   ├── exceptions/            # Custom exception hierarchy & global Starlette handlers
│   │   ├── custom_exceptions.py    # AppError, NotFoundError, DatabaseError
│   │   └── handlers.py        # Global FastAPI exception handlers
│   ├── memory/                # Multi-tier state management
│   │   ├── redis_memory.py    # Fast sliding-window conversation cache
│   │   ├── postgres_memory.py # Durable cross-session student profile storage
│   │   └── memory_manager.py  # Privacy guardrails & sensitive topic redaction
│   ├── middlewares/           # Context extraction & authentication
│   │   └── auth.py            # Student identity & authorization dependencies
│   ├── models/                # SQLAlchemy 2.0 async relational models
│   │   ├── base.py            # Base declarative class with UUIDMixin & TimestampMixin
│   │   ├── student_records.py # Student, FeeRecord, Scholarship, SupportTicket
│   │   ├── conversation.py    # Conversation session model
│   │   ├── message.py         # Turn-by-turn message log model
│   │   ├── student_memory.py  # Long-term extracted student facts
│   │   └── document.py        # Ingested PDF file tracking model
│   ├── prompts/               # Prompt engineering templates
│   │   └── system_prompt.py   # System prompt with role, tone, and injected memories
│   ├── routes/                # FastAPI APIRouter endpoints
│   │   ├── ingestion_routes.py# File upload & document tracking endpoints
│   │   └── index.py           # API v1 aggregator router
│   ├── schemas/               # Pydantic DTOs & OpenAI JSON tool schemas
│   │   ├── chat_schemas.py    # ChatRequest, ChatResponse, CitationDTO
│   │   └── tool_schemas.py    # OpenAI function calling definitions
│   ├── services/              # Domain service layer
│   │   └── ingestion_service.py # Coordinates parse -> chunk -> embed -> Qdrant -> DB
│   ├── tools/                 # Real database tools called by the agent
│   │   ├── student_tools.py   # Async queries for fees, scholarships, and tickets
│   │   └── rag_tool.py        # Semantic vector search on student handbook
│   ├── utils/                 # Utilities & logging
│   │   ├── logger.py          # Loguru rotating file & console handler
│   │   └── response.py        # Standardized API response formatters
│   ├── main.py                # FastAPI app creation & terminal CLI mode
│   └── server.py              # Uvicorn ASGI server entrypoint
├── data/                      # Local PDF handbook & mock json data
├── docker-compose.yml         # Container definitions: postgres:16, redis:7, qdrant:latest
├── evaluation/                # Ingestion fidelity & agent benchmark suites
│   ├── evaluate_chunking.py   # 5-dimension chunking auditor
│   └── results/               # Markdown audit reports & evaluation hub index
├── scripts/                   # CLI maintenance scripts (init_db, seed_db, ingest_handbook)
├── traces/                    # Local turn-by-turn tracer logs (traces/*.json)
└── tracing/                   # LocalTurnTracer implementation
```

---

## 👥 Seeded Test Student Personas

To test different real-world scenarios, the PostgreSQL database is populated via `just seed` with 5 distinct student records:

| Student ID | Name | Programme | Fee Status | Scholarship | Recommended Test Query |
|---|---|---|---|---|---|
| **`STU001`** | **Rahul Sharma** | PGDM AI & DS | Partially Paid (₹225k pending, due Oct 31) | 20% Merit Scholarship (Active) | *"What is my remaining fee balance and my scholarship details?"* |
| **`STU002`** | **Priya Patel** | MBA Marketing | Paid in Full (₹0 balance, RCP-2026-0810) | None | *"Check if I have any pending fee dues."* |
| **`STU003`** | **Amit Verma** | B.Tech CSE | **Overdue** (₹200k pending since Sept 1) | 15% Sports Scholarship (Active) | *"What happens if my fees are overdue and how much do I owe?"* |
| **`STU004`** | **Sneha Gupta** | M.Tech Data Science | Unpaid (₹380k pending, due Nov 15) | 25% Research Fellowship (Active) | *"Can I raise a ticket regarding fee installment extensions?"* |
| **`STU005`** | **Vikram Singh** | BBA | Paid in Full (₹0 balance, RCP-2026-0720) | None | *"What are the library timings and borrowing rules?"* |

---

## 🧠 Dual-Tier Memory Mechanics

The agent implements a privacy-first, dual-tier memory system:

```
[User Input] 
     │
     ▼
┌───────────────────────────────────────────────┐
│ 1. Redis Short-Term Sliding Window (TTL: 24h) │  <-- Stores last 10 turns of active conversation
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│ 2. Sensitive Keyword Redaction Gatekeeper     │  <-- Blocks: medical, grievance, password, stipend,
└──────────────────────┬────────────────────────┘      disciplinary, harassment, bank account
                       │
                       ▼ (Filtered, Non-Sensitive Facts Only)
┌───────────────────────────────────────────────┐
│ 3. PostgreSQL Durable Profile Memories        │  <-- Persistent student preferences, career goals,
└───────────────────────────────────────────────┘      and academic interests across sessions
```

---

## 🛡️ Enterprise Security & Guardrail Architecture

The agent implements a defense-in-depth security model:
1. **JWT Authentication & Passwords**: Passwords hashed using PBKDF2 with SHA-256 (310,000 rounds). Token verification via `get_current_student` dependency.
2. **Code-Level Ownership Enforcement**: Enforced directly inside tool functions (`app/utils/ownership.py`). Regardless of what the student prompt says, an authenticated caller `STU001` cannot read or query data belonging to `STU002`.
3. **Approval Gate for Sensitive Actions**: Human-in-the-loop confirmation required before modifying student records or submitting grievance/appeal tickets.
4. **Immutable Audit Trails**: Every tool invocation and access decision (`ALLOWED`, `BLOCKED`, `APPROVED`, `REJECTED`) is recorded synchronously in PostgreSQL table `audit_logs`.

---

## 🌐 API Endpoint Contracts

### 1. Authentication
- `POST /api/v1/auth/signup` — Enrolled student self-service credential creation.
- `POST /api/v1/auth/login` — Authenticates credentials and returns JWT bearer token.

### 2. Conversational Agent
- `POST /api/v1/chat` — Multi-turn agent turn execution with tool calling and two-tier memory context.
- `GET /api/v1/chat/conversations` — Lists conversation sessions owned by the authenticated student.
- `GET /api/v1/chat/conversations/{id}/messages` — Retrieves turn history for a conversation.

### 3. Student Academic Records (Protected via JWT)
- `GET /api/v1/student/profile` — Authenticated student profile (program, batch, status, CGPA).
- `GET /api/v1/student/fees` — Tuition, hostel, and library fee ledger breakdown.
- `GET /api/v1/student/scholarship` — Active scholarship awards and grant dates.
- `GET /api/v1/student/tickets` — Support tickets opened by the student.

### 4. Audit & Compliance
- `GET /api/v1/audit/logs?limit=50` — Recent security event log stream.
- `GET /api/v1/audit/summary` — Aggregated counts for Allowed, Blocked, and Approved actions.

### 5. Document Ingestion
- `POST /api/v1/ingest/upload` — Multipart form PDF upload, chunking, local embedding, and Qdrant upsert.

### 6. Service Health Check
- `GET /health` — Verifies connection to PostgreSQL, Redis, and Qdrant.

---

## 📊 Benchmark Evaluation Results

The test suite evaluates 8 benchmark scenarios covering tool selection, policy RAG, persistent memory recall, privacy scrubbing, ownership blocking, and domain guardrails.

```bash
just eval    # Executes full benchmark evaluation
```

| ID | Scenario Description | Student | Expected Tool | Tool Precision | Status |
|:---|:---------------------|:-------:|:--------------|:--------------:|:------:|
| 1 | Fee status check | `STU001` | `get_fee_status` | ✅ YES | **PASS** |
| 2 | Payment policy from handbook | `STU001` | `search_student_handbook` | ✅ YES | **PASS** |
| 3 | Scholarship inquiry | `STU001` | `check_scholarship` | ✅ YES | **PASS** |
| 4 | Support ticket creation | `STU001` | `create_support_ticket` | ✅ YES | **PASS** |
| 5 | Cross-student access rejection (Security) | `STU001` | `get_fee_status` | ✅ YES | **PASS** |
| 6 | Persistent memory recall across turns | `STU004` | `None (Direct LLM)` | ✅ YES | **PASS** |
| 7 | Sensitive credentials scrubbing (Privacy) | `STU001` | `None (Direct LLM)` | ✅ YES | **PASS** |
| 8 | Out of scope domain refusal | `STU001` | `None (Direct LLM)` | ✅ YES | **PASS** |

**Benchmark Summary**: **8 / 8 Scenarios Passed (100.0%)**

---

## ⚙️ Environment Variables Reference

| Variable Name | Default Value | Description |
|---|---|---|
| `APP_ENV` | `development` | Runtime environment (`development`, `production`, `testing`) |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async connection string for PostgreSQL 16 |
| `REDIS_URL` | `redis://localhost:6379/0` | Async connection string for Redis 7 |
| `QDRANT_URL` | `http://localhost:6333` | Host URL for Qdrant vector database |
| `EMBEDDING_MODEL` | `Orange/orange-nomic-v1.5-1536` | Local HuggingFace sentence transformer model |
| `EMBEDDING_DIMENSIONS` | `1536` | Embedding vector size (matches Qdrant collection) |
| `CHUNK_TARGET_CHARS` | `1800` | Dynamic target chunk size in characters (~450 tokens) |
| `CHUNK_OVERLAP_CHARS` | `200` | Boundary overlap between adjacent chunks |
| `GROQ_API_KEY` | *(Secret)* | Groq API Key for Llama 3.3 70B inference |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Primary LLM model used for the agent loop |

---

## ⚡ Developer Automation (`Justfile`)

All routine operations are automated via `just`:

```bash
just up             # Start PostgreSQL, Redis, and Qdrant in Docker
just down           # Stop and tear down local containers
just db-init        # Run schema migrations to create all PostgreSQL tables
just seed           # Seed the 5 test student records, fees, and scholarships
just ingest         # Parse, chunk, embed, and index student handbook into Qdrant
just eval           # Run 8 benchmark evaluation scenarios and generate markdown report
just audit-chunks   # Execute 5-dimension chunking fidelity auditor
just server         # Start FastAPI server with hot-reload (localhost:8000)
just streamlit      # Launch Streamlit interactive dashboard UI
just cli            # Launch interactive terminal chat agent
just clean          # Remove cache files, temporary test logs, and bytecodes
```

