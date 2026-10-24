# Intelligent Student Support Agent 🎓

[![React 19](https://img.shields.io/badge/Frontend-React_19_+_Vite-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16_(Docker)-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis 7](https://img.shields.io/badge/Redis-7_(Docker)-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_Store-DC2626?logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Groq Llama 3.3 70B](https://img.shields.io/badge/Groq-Llama_3.3_70B-F55036)](https://groq.com)
[![Dynamic Fallback](https://img.shields.io/badge/Fallback-Qwen_2.5_32B-8A2BE2)](https://groq.com)
[![Chunking Fidelity](https://img.shields.io/badge/Chunking_Fidelity-100%25_PASS-success)](Intelligent_Student_Support_Agent/evaluation/results/chunking_audit_report.md)

> **End-Term Capstone Project: Agentic AI Engineering**  
> An autonomous, enterprise-grade multi-turn conversational AI student support platform. Combines structure-aware policy RAG (from the 44-page official university handbook) with live PostgreSQL database tools (fees, scholarships, grievance tickets), stateful dual-tier memory (Redis L1 cache + PostgreSQL L2 permanent facts), dynamic multi-model fallback (`qwen/qwen3.8-27b`), and a responsive React 19 web portal.

---

## 📌 Master Documentation Hub

| Documentation Guide | Focus Area & Description |
|---|---|
| 📡 **[Full REST API Documentation (`API_DOCUMENTATION.md`)](./Intelligent_Student_Support_Agent/API_DOCUMENTATION.md)** | Complete specification for all 17 REST endpoints with exact schemas, status codes, OWASP security headers, and copy-pasteable `curl` commands. |
| 🏛️ **[Backend Core Architectural Guide (`Intelligent_Student_Support_Agent/README.md`)](./Intelligent_Student_Support_Agent/README.md)** | Deep Clean Architecture overview, 20 pre-seeded student personas, Option 2 self-enrollment mechanics, and dual-tier memory privacy gates. |
| 📁 **[Subpackage Architecture Guides (All 15 Backend Modules)](./Intelligent_Student_Support_Agent/README.md#-module-documentation-index)** | Clickable guides with dedicated Mermaid flowcharts for `routes`, `controllers`, `services`, `agent`, `providers`, `memory`, `tools`, `ai`, and more. |
| 🖥️ **[Frontend Student Portal (`Frontend/student-portal/README.md`)](./Intelligent_Student_Support_Agent/Frontend/student-portal/README.md)** | Modern React 19 + Vite student portal setup, authentication state, interactive chat UI, and responsive fee/profile dashboards. |
| 🛡️ **[Security Hardening & Backend Audit Report (`BACKEND_AUDIT_REPORT.md`)](./Intelligent_Student_Support_Agent/BACKEND_AUDIT_REPORT.md)** | Production readiness verification: OWASP Top 10 API Security, sliding-window rate limiting, pure PostgreSQL connection pooling, and zero SQLite compliance. |

---

## 🏛️ Full-Stack Monorepo Architecture

The workspace implements a decoupled, modern multi-tier topology separating the frontend presentation layer, backend API gateway, persistent containerized storage, and external AI inference services:

```mermaid
flowchart TD
    subgraph ClientLayer["1. Client Presentation Tier"]
        Portal["Web Student Portal<br/>(React 19 + Vite + Tailwind CSS)<br/>http://localhost:3000"]
        TerminalCLI["Terminal CLI Agent<br/>(scripts/cli.py)<br/>just cli"]
    end

    subgraph GatewayLayer["2. Backend Application Gateway (Port 8000)"]
        FastAPI["FastAPI REST Application Gateway<br/>(Intelligent_Student_Support_Agent/app/)<br/>• Declarative RESTful Routes & Pydantic v2 DTOs<br/>• OWASP Security Headers (nosniff, DENY)<br/>• Sliding-Window Rate Limiter (Chat: 30/min, Login: 20/min)<br/>• HS256 JWT Authentication & Tenant Ownership Guard"]
        
        AgentCore["ReAct Conversational Agent Core<br/>• Multi-turn reasoning loop (agent_loop.py)<br/>• LLMFactory dynamic fallback orchestrator<br/>• Local execution tracer (traces/*.json)"]
    end

    subgraph CloudAI["3. External AI Model Inference"]
        GroqPrimary["Primary Groq Model<br/>(llama-3.3-70b-versatile / gpt-oss-120b)"]
        GroqFallback["Dynamic Fallback Model<br/>(qwen/qwen3.8-27b)"]
    end

    subgraph DataLayer["4. Containerized Persistence Infrastructure (Docker)"]
        Postgres[("PostgreSQL 16 DB<br/>• students, auth_credentials<br/>• fee_records, scholarships<br/>• support_tickets, audit_logs<br/>• Durable student_memory (L2)")]
        Redis[("Redis 7 Cache<br/>• L1 Sliding Window Memory<br/>• Sliding-Window Rate Limit Keys<br/>• Sub-Second RAG Query Cache")]
        Qdrant[("Qdrant Vector DB<br/>• student_handbook Collection<br/>• 1536-dim Cosine Similarity<br/>• Orange/orange-nomic-v1.5")]
    end

    Portal -->|"HTTP / REST (Bearer JWT)"| FastAPI
    TerminalCLI -->|"Local Direct Invocation"| FastAPI
    FastAPI --> AgentCore

    AgentCore <-->|"Primary Inference"| GroqPrimary
    AgentCore -.->|"Automated Failover"| GroqFallback

    AgentCore -->|"Tuition, Scholarships, Tickets"| Postgres
    AgentCore -->|"L1 Conversation Context"| Redis
    AgentCore -->|"Handbook Semantic Search"| Qdrant
    FastAPI -->|"Relational Queries & Auth"| Postgres
```

---

## 🔄 Turn-by-Turn Conversational Interaction Flow

Every student interaction passes through an autonomous multi-turn reasoning and tool-calling cycle:

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student (Web Portal / API)
    participant Gateway as FastAPI Gateway (:8000)
    participant Mem as Memory Manager (Redis + Postgres)
    participant Agent as ReAct Agent Loop (LLMFactory)
    participant Tools as Domain Tools (DB / RAG)
    participant DB as PostgreSQL / Redis / Qdrant

    Student->>Gateway: POST /api/v1/chat "What is my pending fee balance and the late payment fee?"
    Gateway->>Gateway: Validate Bearer JWT & Check Rate Limit (30 req/min)
    Gateway->>Mem: Load active conversation history (Redis L1) + profile facts (Postgres L2)
    Mem-->>Gateway: Active turns + student preferences
    Gateway->>Agent: Launch ReAct loop with injected context & tool schemas
    
    rect rgb(240, 248, 255)
        Note over Agent, Tools: Iteration 1: Autonomous Reasoning & Database Inspection
        Agent->>Tools: Call get_fee_status(student_id="STU001")
        Tools->>DB: Query fee_records in PostgreSQL
        DB-->>Tools: {"total_fee": 450000, "paid": 225000, "pending": 225000, "due_date": "2026-10-31"}
        Tools-->>Agent: Observation: ₹2,25,000 pending due on Oct 31, 2026
    end

    rect rgb(255, 250, 240)
        Note over Agent, Tools: Iteration 2: Policy Handbook Vector Search (Sub-Second RAG)
        Agent->>Tools: Call search_student_handbook(query="late fee payment surcharge penalty")
        Tools->>DB: Cosine search in Qdrant / Redis Cache (2.3 ms)
        DB-->>Tools: Section 4.2 | Page 12: "Late fee surcharge is ₹500/day up to 15 days..."
        Tools-->>Agent: Observation: Policy text & citation
    end

    Note over Agent, Mem: Iteration 3: Final Response Synthesis & State Persistence
    Agent->>Mem: Update sliding conversation window in Redis
    Agent->>Mem: Extract non-sensitive facts for durable storage in Postgres
    Agent-->>Gateway: Synthesized reply with exact citations & execution trace ID
    Gateway-->>Student: 200 OK Uniform JSON Response Envelope
```

---

## 📂 Repository Directory Layout

```text
Agentic_AI_End_Term_Project/
├── Intelligent_Student_Support_Agent/         # Core Backend & Full Application Package
│   ├── app/
│   │   ├── agent/                             # Multi-turn ReAct loop & LLM client provider
│   │   ├── ai/                                # PDF parsing, semantic chunking, local embedder & vector store
│   │   ├── config/                            # BaseSettings (.env), PostgreSQL connection pool, Redis client
│   │   ├── controllers/                       # HTTP request controllers (Auth, Student, Chat, Audit, Ingest)
│   │   ├── exceptions/                        # Domain AppError hierarchy & global exception handlers
│   │   ├── memory/                            # Dual-tier memory facade (Redis L1 + PostgreSQL L2)
│   │   ├── middlewares/                       # JWT auth, OWASP security headers, sliding-window rate limiter
│   │   ├── models/                            # SQLAlchemy 2.0 async models (8 domain tables)
│   │   ├── prompts/                           # Dynamic system prompt builder with injected memories & dates
│   │   ├── providers/                         # Multi-provider LLM factory & dynamic fallback (qwen/qwen3.8-27b)
│   │   ├── routes/                            # Declarative FastAPI endpoints (/auth, /student, /chat, etc.)
│   │   ├── schemas/                           # Pydantic v2 DTOs for request/response payloads
│   │   ├── services/                          # Core domain business logic services
│   │   ├── tools/                             # Real database & vector tools with ownership guardrails
│   │   ├── utils/                             # Deep health probes, Loguru logging, response formatters
│   │   ├── main.py                            # FastAPI factory, lifespan pre-warming, and middleware setup
│   │   └── server.py                          # Uvicorn production launcher
│   ├── Frontend/student-portal/               # React 19 + Vite + Tailwind CSS Web Portal
│   ├── data/                                  # Official 44-page university student handbook PDF
│   ├── docker-compose.yml                     # Multi-container stack (PostgreSQL 16, Redis 7, Qdrant)
│   ├── evaluation/                            # Chunking fidelity evaluator & 8-scenario benchmark test suite
│   ├── scripts/                               # CLI runner, DB seeders, handbook ingestion runner
│   ├── alembic/                               # Alembic versioned migrations tracked in git
│   ├── API_DOCUMENTATION.md                   # Complete RESTful API specification (17 endpoints)
│   ├── BACKEND_AUDIT_REPORT.md                # Certified backend code review & security audit report
│   ├── Dockerfile                             # Multi-stage production container image with non-root appuser
│   ├── pyproject.toml                         # Python dependencies, Ruff linter, and Mypy configurations
│   └── Justfile                               # Backend task automation recipes
├── .gitignore                                 # Monorepo gitignore configuration
├── Justfile                                   # Root task automation recipes (navigates subdirs automatically)
└── README.md                                  # Repository master overview (this document)
```

---

## ⚡ Developer Quickstart (`Justfile`)

All routine operations can be executed directly from the repository root using the automated task runner `just`:

### 1. Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running)
- [uv](https://docs.astral.sh/uv/) (Python 3.12 package runner)
- [Node.js 18+](https://nodejs.org/) & `npm`
- [Just](https://github.com/casey/just)

### 2. Configure Environment
Copy `.env.example` into `.env` inside `Intelligent_Student_Support_Agent/`:
```bash
cp Intelligent_Student_Support_Agent/.env.example Intelligent_Student_Support_Agent/.env
```
Ensure your `GROQ_API_KEY` is configured in `.env`.

### 3. Bootstrap & Launch
```bash
# 1. Start Docker containers (PostgreSQL 16, Redis 7, Qdrant)
just up

# 2. Initialize PostgreSQL schema & stamp Alembic migrations
just db-init

# 3. Seed 20 comprehensive student accounts into PostgreSQL
just seed

# 4. Parse, chunk, and vectorize the 44-page handbook into Qdrant
just ingest

# 5. Launch FastAPI Backend Server (http://localhost:8000)
just server

# 6. Launch Frontend Student Portal in a separate terminal (http://localhost:3000)
just frontend
```

---

## 🛠️ Complete Agent Tool Suite (8 Domain Tools)

Every tool enforces **strict code-level tenant ownership** via `check_ownership(caller, target)`. Cross-student data inquiries immediately return a security block and write an immutable record to `audit_logs`:

| Tool Function | Target Subsystem | Ownership Guard | Description |
|---|---|:---:|---|
| **`get_fee_status(student_id)`** | PostgreSQL (`fee_records`) | Strict Student Match | Tuition dues, installments paid, pending balance, and payment receipts. |
| **`check_scholarship(student_id)`** | PostgreSQL (`scholarships`) | Strict Student Match | Active grant schemes, concession percentages, and semester grant values. |
| **`create_support_ticket(student_id, category, description, priority)`** | PostgreSQL (`support_tickets`) | Strict Student Match | Creates an official administrative escalation ticket with UUID tracking. |
| **`get_ticket_status(ticket_id)`** | PostgreSQL (`support_tickets`) | Strict Student Match | Looks up resolution status and priority for a specific ticket. |
| **`list_student_tickets(student_id)`** | PostgreSQL (`support_tickets`) | Strict Student Match | Retrieves all active and historical tickets filed by the student. |
| **`update_student_profile(student_id, phone, email, address)`** | PostgreSQL (`students`) | Authenticated Session | Immediately updates student contact coordinates in university records. |
| **`update_student_password(student_id, new_password)`** | PostgreSQL (`auth_credentials`) | Authenticated Session | Updates student credentials immediately in PostgreSQL with bcrypt hashing. |
| **`search_student_handbook(query, section_filter)`** | Qdrant Vector DB | Public Domain | Sub-second semantic vector search over student handbook policies with citations. |

---

## 📊 Benchmark Evaluation Results

The test suite evaluates 8 benchmark scenarios covering tool selection, policy RAG, persistent memory recall, privacy scrubbing, ownership blocking, and domain guardrails (`just eval`):

| ID | Scenario Description | Student | Expected Tool | Precision | Status |
|:---:|:---|:---:|:---|:---:|:---:|
| 1 | Fee status check | `STU001` | `get_fee_status` | ✅ YES | **PASS** |
| 2 | Payment policy from handbook | `STU001` | `search_student_handbook` | ✅ YES | **PASS** |
| 3 | Scholarship inquiry | `STU001` | `check_scholarship` | ✅ YES | **PASS** |
| 4 | Support ticket creation | `STU001` | `create_support_ticket` | ✅ YES | **PASS** |
| 5 | Cross-student access rejection (Security) | `STU001` | `get_fee_status` | ✅ YES | **PASS** |
| 6 | Persistent memory recall across turns | `STU004` | `None (Direct LLM)` | ✅ YES | **PASS** |
| 7 | Sensitive credentials scrubbing (Privacy) | `STU001` | `None (Direct LLM)` | ✅ YES | **PASS** |
| 8 | Out of scope domain refusal | `STU001` | `None (Direct LLM)` | ✅ YES | **PASS** |

**Benchmark Score**: **8 / 8 Scenarios Passed (100.0%)**

---

## 👥 Student Test Personas & Option 2 Enrollment

The PostgreSQL database is pre-seeded with **20 comprehensive student records** (`STU001` through `STU020`) via `just seed`:

* **Pre-Activated Demo Accounts (`STU001`–`STU005`)**: Initialized with default password `Student@123` for instant portal login and testing.
* **Available Registration Cohort (`STU006`–`STU020`)**: Enrolled in university records but awaiting account creation. Users register them via `/signup`.
* **Negative Test Persona (`STU999`)**: Not enrolled in university roster. Attempting registration returns `404 Not Found`.

| Student ID | Name | Programme | Fee Status | Scholarship | Account State | Testing Scenario |
|:---:|---|---|---|---|:---:|---|
| **`STU001`** | **Rahul Sharma** | PGDM AI & DS | Partially Paid (₹225k due Oct 31) | 20% Merit (Active) | Pre-Activated (`Student@123`) | Fee balance, handbook refund policies, and scholarship inquiries. |
| **`STU002`** | **Priya Patel** | MBA Marketing | Paid in Full (₹0 due, RCP-0810) | None | Pre-Activated (`Student@123`) | Paid-in-full queries and verification of cross-student block from `STU001`. |
| **`STU003`** | **Amit Verma** | B.Tech CSE | **Overdue** (₹200k since Sept 1) | 15% Sports (Active) | Pre-Activated (`Student@123`) | Overdue penalty inquiry and handbook disciplinary grace periods. |
| **`STU004`** | **Sneha Gupta** | M.Tech Data Science | Unpaid (₹380k due Nov 15) | 25% Research (Active) | Pre-Activated (`Student@123`) | Support ticket escalation testing and multi-turn memory recall. |
| **`STU005`** | **Vikram Malhotra** | BBA Analytics | Partially Paid (₹150k due Dec 1) | None | Pre-Activated (`Student@123`) | General administrative inquiries and profile contact updates. |
| **`STU006`** | **Ananya Iyer** | B.Tech AI & ML | Partially Paid (₹210k due Nov 30) | 30% Women in Tech | Available for `/signup` | Self-service Option 2 enrollment verification. |
| **`STU007`–`STU020`**| *Enrolled Cohort* | Diverse UG / PG | Mixed (Paid, Overdue, Pending) | Various | Available for `/signup` | Comprehensive enrollment testing across cohorts. |

---

*Project engineered for Advanced Agentic AI Engineering Capstone. Verified against running PostgreSQL, Redis, and Qdrant container infrastructure.*
