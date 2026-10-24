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

## 👥 Seeded Test Student Personas (Option 2 Architecture)

The PostgreSQL database is seeded via `just seed` with **20 comprehensive student records** (`STU001` through `STU020`) containing academic profiles, fee ledgers, scholarship grants, and support tickets:

- **Pre-Configured Instant Login (`STU001` – `STU005`)**: Credentials pre-initialized with password `Student@123` for instant testing and demonstration.
- **Available Registration Roster (`STU006` – `STU020`)**: Enrolled university records exist in PostgreSQL, ready to be claimed by users via `/signup`.

| Student ID | Name | Programme | Fee Status | Scholarship | Account State | Recommended Test Query / Action |
|---|---|---|---|---|:---:|---|
| **`STU001`** | **Rahul Sharma** | PGDM AI & DS | Partially Paid (₹225k pending, due Oct 31) | 20% Merit (Active) | Pre-Activated | *"What is my remaining fee balance and my scholarship details?"* |
| **`STU002`** | **Priya Patel** | MBA Marketing | Paid in Full (₹0 balance, RCP-2026-0810) | None | Pre-Activated | *"Check if I have any pending fee dues."* |
| **`STU003`** | **Amit Verma** | B.Tech CSE | **Overdue** (₹200k pending since Sept 1) | 15% Sports (Active) | Pre-Activated | *"What happens if my fees are overdue and how much do I owe?"* |
| **`STU004`** | **Sneha Gupta** | M.Tech Data Science | Unpaid (₹380k pending, due Nov 15) | 25% Research (Active) | Pre-Activated | *"Can I raise a ticket regarding fee installment extensions?"* |
| **`STU005`** | **Vikram Singh** | BBA | Paid in Full (₹0 balance, RCP-2026-0720) | None | Pre-Activated | *"What are the library timings and borrowing rules?"* |
| **`STU006`** | **Ananya Iyer** | B.Tech AI & ML | Partially Paid (₹210k pending, due Nov 30) | 30% Women in Tech | Available | Test `/signup` with password `Password@123`, then view dashboard. |
| **`STU007`–`STU020`** | *Enrolled Cohort* | Diverse UG/PG | Mixed (Paid, Overdue, Pending) | Merit & Need-based | Available | Self-registration testing across different degree programmes. |

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
1. **JWT Authentication & Passwords**: Passwords hashed using bcrypt. Stateless JWT verification via FastAPI `get_current_student` dependency.
2. **Code-Level Ownership Enforcement**: Enforced directly inside tool functions (`app/utils/ownership.py`). Regardless of what the student prompt says, an authenticated caller `STU001` cannot read or query data belonging to `STU002`.
3. **Approval Gate for Sensitive Actions**: Human-in-the-loop confirmation required before modifying student records or submitting grievance/appeal tickets.
4. **Immutable Audit Trails**: Every tool invocation and access decision (`ALLOWED`, `BLOCKED`, `APPROVED`, `REJECTED`) is recorded synchronously in PostgreSQL table `audit_logs`.

---

## 🌐 API Endpoint Contracts & Live Verification

### 1. Authentication (`/api/v1/auth`)
- **`POST /api/v1/auth/signup`** — Enrolled student self-service credential creation (Option 2).
  - *Request Body*: `{"student_id": "STU006", "password": "Password@123"}`
  - *Validation*: Requires student to exist in university PostgreSQL `students` table. Rejects non-enrolled IDs (`404`) and duplicate accounts (`409`).
  - *Response (`201 Created`)*: `{"status": "success", "message": "Student account registered successfully.", "data": {"student_id": "STU006"}}`
- **`POST /api/v1/auth/login`** — Authenticates student credentials and returns a Bearer JWT token.
  - *Request Body*: `{"student_id": "STU006", "password": "Password@123"}`
  - *Response (`200 OK`)*: `{"status": "success", "data": {"access_token": "<JWT>", "token_type": "bearer", "expires_in": 86400}}`

### 2. Student Academic Records (`/api/v1/student`, Protected via Bearer JWT)
- **`GET /api/v1/student/profile`** — Authenticated student profile (name, programme, batch, status, contact).
- **`GET /api/v1/student/fees`** — Tuition and fee ledger breakdown (total fee, paid, pending, due date, receipt).
- **`GET /api/v1/student/scholarship`** — Active scholarship awards, percentage, and grant amount.
- **`GET /api/v1/student/tickets`** — Support and grievance tickets logged by the authenticated student.
- **`PUT /api/v1/student/profile`** — Update student contact information (phone, email, address) directly in PostgreSQL.

### 3. Conversational Agent (`/api/v1/chat`, Protected via Bearer JWT)
- **`POST /api/v1/chat`** — Multi-turn agent execution with semantic RAG tool-calling and two-tier memory.
- **`GET /api/v1/chat/conversations`** — Lists conversation sessions owned by the authenticated student.
- **`GET /api/v1/chat/conversations/{id}/messages`** — Retrieves turn history for a conversation.

### 4. Audit & Compliance (`/api/v1/audit`)
- **`GET /api/v1/audit/logs?limit=50`** — Recent security event log stream.
- **`GET /api/v1/audit/summary`** — Aggregated counts for Allowed, Blocked, and Approved actions.

### 5. Document Ingestion (`/api/v1/ingest`)
- **`POST /api/v1/ingest/upload`** — Multipart form PDF upload, chunking, local embedding, and Qdrant upsert.

### 6. Service Health Check
- **`GET /health`** — Verifies connection to PostgreSQL, Redis, and Qdrant (`{"status": "ok"}`).

---

### 📊 Live API Verification Matrix (PostgreSQL Backend)

The table below summarizes live integration test results executed against the running backend with Docker PostgreSQL:

| Endpoint & Method | Test Scenario | HTTP Status | Response Summary | Architectural Invariant Verified |
|:---|:---|:---:|:---|:---|
| `POST /api/v1/auth/signup` | Unregistered ID `STU999` | **404 Not Found** | `"Student ID 'STU999' is not enrolled in the university records. Registration requires an enrolled Student ID (STU001 through STU020)."` | **Option 2 Gatekeeper**: Non-enrolled users are prevented from creating rogue accounts. |
| `POST /api/v1/auth/signup` | Enrolled ID `STU006` | **201 Created** | `"Student account registered successfully."` | **Credential Creation**: Hashes password with bcrypt and records in PostgreSQL `auth_credentials`. |
| `POST /api/v1/auth/signup` | Duplicate `STU006` | **409 Conflict** | `"An account for student ID 'STU006' already exists. Please log in."` | **Collision Guard**: Idempotently prevents account overwrites. |
| `POST /api/v1/auth/login` | Login with `STU006` | **200 OK** | Returned valid signed Bearer JWT token | **JWT Lifecycle**: Issues signed token with claim `sub: STU006`. |
| `GET /api/v1/student/profile` | Bearer Token for `STU006` | **200 OK** | Loaded: Ananya Iyer, B.Tech AI & ML, Batch 2024-28 | **Referential Integrity**: Links JWT subject to PostgreSQL `students` table. |
| `GET /api/v1/student/fees` | Bearer Token for `STU006` | **200 OK** | Loaded: Total ₹4,20,000, Partially Paid, RCP-2026-0412 | **Ledger Isolation**: Resolves pre-seeded fee ledger for student. |
| `GET /api/v1/student/scholarship` | Bearer Token for `STU006` | **200 OK** | Loaded: Women in Tech Award (30% / ₹63,000) | **Aid Grant Resolution**: Fetches active award from PostgreSQL `scholarships`. |
| `GET /api/v1/student/tickets` | Bearer Token for `STU006` | **200 OK** | Retrieved 0 support tickets (clean initial state) | **Tenant Boundary**: Returns only tickets belonging to authenticated student. |

> Detailed audit logs and metrics are documented in [evaluation/results/auth_audit_report.md](file:///d:/Agentic_AI_End_Term_Project/Intelligent_Student_Support_Agent/evaluation/results/auth_audit_report.md).

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
| `GROQ_API_KEY` | *(Secret)* | Groq API Key for openai/gpt-oss-120b inference |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Primary LLM model used for the agent loop |

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

