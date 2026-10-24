# ⚙️ Services Layer (`app/services`)

The **Services Layer** contains the core domain logic, transactional rules, identity lifecycles, and agent orchestration routines of the system. It strictly isolates business workflows from both HTTP transport concerns and raw database driver details.

---

## 🏗️ Domain Service Architecture

```mermaid
flowchart TD
    Ctrl["Controllers / API Inbound Request"] --> Services["Domain Services Layer (app/services/)"]

    subgraph ServiceCatalog["Domain Business Logic Services"]
        direction TB
        AuthSvc["AuthService<br/>• Option 2 Roster Verification<br/>• bcrypt Hashing & JWT Token Lifecycle"]
        ChatSvc["ChatService<br/>• Multi-Turn ReAct Agent Orchestration<br/>• Dynamic Fallback & Memory Injection"]
        StudentSvc["StudentService<br/>• Profile, Ledger & Scholarship Queries<br/>• Contact Detail Updates in PostgreSQL"]
        ApprovalSvc["ApprovalService<br/>• Human-in-the-Loop Sensitive Action Gate<br/>• Confirmation / Rejection Decisions"]
        AuditSvc["AuditService<br/>• Immutable Security Trail Logging<br/>• Compliance Metrics (ALLOWED, BLOCKED)"]
        IngestSvc["IngestionService<br/>• PDF Handbook Parsing & Semantic Chunking<br/>• 1536-dim Embedding Vectorization"]
    end

    Services --> AuthSvc
    Services --> ChatSvc
    Services --> StudentSvc
    Services --> ApprovalSvc
    Services --> AuditSvc
    Services --> IngestSvc

    subgraph StorageLayer["Infrastructure & Persistence (Docker)"]
        Postgres[("PostgreSQL 16 DB<br/>• students, auth_credentials<br/>• fee_records, scholarships, audit_logs")]
        Redis[("Redis 7 Cache<br/>• L1 Sliding Window Memory<br/>• Rate Limit Counters & RAG Cache")]
        Qdrant[("Qdrant Vector DB<br/>• student_handbook Collection<br/>• 1536-dim Cosine Similarity")]
    end

    AuthSvc --> Postgres
    StudentSvc --> Postgres
    ApprovalSvc --> Postgres
    AuditSvc --> Postgres
    ChatSvc --> Postgres
    ChatSvc --> Redis
    ChatSvc --> Qdrant
    IngestSvc --> Qdrant
    IngestSvc --> Postgres
```

---

## 📁 Module Inventory

| File | Service Class | Primary Domain Responsibilities |
|---|---|---|
| [`auth_service.py`](./auth_service.py) | `AuthService` | Verifies university enrollment (Option 2), hashes passwords with bcrypt, signs JWT tokens, and validates student credentials. |
| [`chat_service.py`](./chat_service.py) | `ChatService` | Manages the end-to-end conversational agent loop: memory retrieval, OpenAI function calling, database tool dispatch, and citation assembly. |
| [`student_service.py`](./student_service.py) | `StudentService` | Retrieves authenticated student directory info, fee payment ledgers, active scholarship awards, and support tickets from PostgreSQL. |
| [`approval_service.py`](./approval_service.py) | `ApprovalService` | Evaluates whether sensitive student requests (e.g., fee installment extension, profile updates) require human administrative review. |
| [`audit_service.py`](./audit_service.py) | `AuditService` | Writes tamper-resistant audit records (`audit_logs` table) for security events, tool executions, and access control blocks. |
| [`ingestion_service.py`](./ingestion_service.py) | `IngestionService` | Orchestrates handbook PDF document processing: parsing, recursive semantic chunking, dense embedding, and vector upsert into Qdrant. |

---

## 💎 SOLID Principles Implementation

1. **Single Responsibility (SRP)**: Each service class is focused on one business capability (e.g., `AuthService` never queries fee ledgers; `StudentService` never generates JWT tokens).
2. **Open/Closed Principle (OCP)**: New tool integrations or audit filters can be added to `ChatService` without refactoring underlying authentication or session management routines.
3. **Dependency Inversion (DIP)**: Services receive an `AsyncSession` during instantiation (`__init__(self, session: AsyncSession)`), facilitating unit testing with mock sessions.
