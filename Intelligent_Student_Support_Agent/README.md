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

## 🌐 API Endpoint Contracts

### 1. Conversational Chat
`POST /api/v1/chat`

**Request Body:**
```json
{
  "student_id": "STU001",
  "message": "What is the minimum attendance required for writing end-term examination?",
  "conversation_id": "optional-uuid"
}
```

**Response Format:**
```json
{
  "success": true,
  "data": {
    "conversation_id": "e3b0c442-98fc-1c14-9afb-4c7c5af8e2b1",
    "response": "According to Section 10.2 of the Student Handbook, a minimum attendance of 70% is required in each course to be eligible to appear for the end-term examination.",
    "citations": [
      {
        "source": "student_handbook.pdf",
        "section_number": "10.2",
        "section_title": "Eligibility for Writing End-Term Examination",
        "page_number": 9
      }
    ],
    "trace_id": "trace-7f28a9b1",
    "turn_latency_ms": 842
  }
}
```

### 2. Document Ingestion
`POST /api/v1/ingest/upload` (Multipart Form: `file: UploadFile`)
- Extracts structured policy sections
- Generates 1536-dimensional embeddings
- Indexes chunks in Qdrant with payload metadata
- Updates document tracking in PostgreSQL (`UPLOADED` ➔ `PROCESSING` ➔ `INSERTED`)

### 3. Service Health Check
`GET /health`
- Verifies connection to PostgreSQL (`SELECT 1`)
- Verifies connection to Redis (`PING`)
- Verifies connection to Qdrant (`get_collections()`)

---

## ⚙️ Environment Variables Reference

| Variable Name | Default Value | Description |
|---|---|---|
| `APP_ENV` | `development` | Runtime environment (`development`, `production`, `testing`) |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async connection string for PostgreSQL 16 |
| `REDIS_URL` | `redis://localhost:6379/0` | Async connection string for Redis 7 |
| `QDRANT_URL` | `http://localhost:6333` | Host URL for Qdrant vector database |
| `EMBEDDING_MODEL_NAME` | `Orange/orange-nomic-v1.5-1536` | Local HuggingFace sentence transformer model |
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
just db-init        # Run schema migrations to create all 8 PostgreSQL tables
just seed           # Seed the 5 test student records, fees, and scholarships
just ingest         # Parse, chunk, embed, and index student handbook into Qdrant
just audit-chunks   # Execute 5-dimension chunking fidelity auditor
just server         # Start FastAPI server with hot-reload (localhost:8000)
just streamlit      # Launch Streamlit interactive developer dashboard
just cli            # Launch interactive terminal chat agent
just clean          # Remove cache files, temporary test logs, and bytecodes
```
