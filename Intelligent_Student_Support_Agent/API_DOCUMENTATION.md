# 📡 Intelligent Student Support Agent: API Documentation

> **Complete RESTful API Specification & Developer Guide**  
> **API Version**: `v1.0.0`  
> **Base URL**: `http://localhost:8000/api/v1`  
> **Interactive Documentation**:
> - Swagger UI: [`http://localhost:8000/docs`](http://localhost:8000/docs)
> - ReDoc UI: [`http://localhost:8000/redoc`](http://localhost:8000/redoc)
> - OpenAPI JSON: [`http://localhost:8000/openapi.json`](http://localhost:8000/openapi.json)

---

## ⚡ Quick Navigation

| Section | Focus Area |
|---|---|
| 🏛️ **[1. Architectural Standards & Security Principles](#1-architectural-standards--security-principles)** | Clean Architecture, SOLID, OWASP headers, sliding-window rate limiting |
| 📋 **[2. Standardized JSON Response Envelopes](#2-standardized-json-response-envelopes)** | Predictable structures for Success (`200`/`201`), Client Error (`4xx`), and Server Error (`5xx`) |
| 🌐 **[3. Master Endpoints Index (17 Endpoints)](#3-master-endpoints-index-17-endpoints)** | Complete route table with methods, auth guards, rate limits, and purposes |
| 🔐 **[4. Authentication & Identity (`/api/v1/auth`)](#4-authentication--identity-apiv1auth)** | Option 2 enrollment, JWT login, credential management, token verification |
| 💬 **[5. Multi-Turn AI Agent Chat (`/api/v1/chat`)](#5-multi-turn-ai-agent-chat-apiv1chat)** | ReAct loop, Groq fallback model (`qwen/qwen3.8-27b`), sub-second RAG, session management |
| 🎓 **[6. Student University Records (`/api/v1/student`)](#6-student-university-records-apiv1student)** | Profile CRUD, tuition fees, scholarships, and support grievance tickets |
| 🔍 **[7. Security Audit & Compliance (`/api/v1/audit`)](#7-security-audit--compliance-apiv1audit)** | Immutable audit trail query and aggregated compliance metrics |
| 📄 **[8. Handbook Document Ingestion (`/api/v1/ingest`)](#8-handbook-document-ingestion-apiv1ingest)** | Multipart PDF parsing, semantic chunking, and Qdrant vectorization |
| 💓 **[9. Deep Health & Diagnostic Probes (`/health`)](#9-deep-health--diagnostic-probes-health)** | Non-blocking async probes across PostgreSQL, Redis, and Qdrant |
| 👥 **[10. Student Test Personas Matrix](#10-student-test-personas-matrix)** | Pre-seeded accounts (`STU001`–`STU020`) and negative test cases (`STU999`) |
| 🚀 **[11. End-to-End Curl Testing Guide](#11-end-to-end-curl-testing-guide)** | Copy-pasteable verification workflows from registration to agent chat |

---

## 1. Architectural Standards & Security Principles

The Intelligent Student Support Agent API is engineered according to enterprise **Clean Architecture** and **SOLID Principles**:

- **Perimeter Defense in Depth**:
  - **OWASP Security Headers**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-XSS-Protection: 1; mode=block`.
  - **CORS Restriction**: Removed wildcard `*` origins; strictly limited to configured frontend origins (`http://localhost:3000`, `http://localhost:5173`).
  - **Sliding-Window Rate Limiting**: Backed by atomic Redis counters (with in-memory fallback):
    - `POST /api/v1/chat`: **30 requests / minute**
    - `POST /api/v1/auth/login`: **20 requests / minute**
- **Authentication & Code-Level Authorization**:
  - Signed HS256 JWT access tokens with 24-hour expiration (`app/middlewares/auth.py`).
  - Strict tenant isolation enforced at the data layer (`app/utils/ownership.py`). Attempting to query cross-student records returns `403 Forbidden` and creates an audit record.
  - Option 2 Student Enrollment: Self-service registration pre-validates student ID against university roster records (`students` table).
- **Two-Tier Memory & Privacy Guard**:
  - Redis L1 cache (24h TTL) + PostgreSQL L2 permanent storage.
  - Sensitive keyword scrubbing automatically removes passwords, OTPs, CVVs, PINs, card numbers, and tokens prior to memory persistence.
- **Dynamic Multi-Provider AI Orchestration**:
  - Decoupled `LLMFactory` (`app/providers/llm/factory.py`) dynamically routes chat turns to primary Groq models with automated fallback to `qwen/qwen3.8-27b` (`groq_fallback_model`).
  - RAG handbook retrieval accelerated via RAM model pre-warming, in-memory LRU query cache, and Redis 24h caching (**2.3 ms cached query latency**).
- **Zero SQLite Compliance**:
  - Pure PostgreSQL connectivity (`pool_size=20, max_overflow=10, pool_pre_ping=True`) with versioned Alembic database migrations.

---

## 2. Standardized JSON Response Envelopes

All HTTP responses conform to consistent JSON envelopes:

### 2.1 Success Envelope (`200 OK`, `201 Created`)
```json
{
  "status": "success",
  "message": "Operation completed successfully.",
  "data": { ... }
}
```

### 2.2 Client Failure Envelope (`400`, `401`, `403`, `404`, `409`, `422`, `429`)
```json
{
  "status": "fail",
  "message": "Student ID 'STU999' is not registered in the university roster.",
  "request_id": "9f8c6e28-48b6-4b48-8df0-184517b6a124",
  "errors": null
}
```

### 2.3 Server Error Envelope (`500 Internal Server Error`, `503 Service Unavailable`)
```json
{
  "status": "error",
  "message": "An unexpected internal server error occurred.",
  "request_id": "9f8c6e28-48b6-4b48-8df0-184517b6a124",
  "errors": "Detailed exception trace logged internally."
}
```

---

## 3. Master Endpoints Index (17 Endpoints)

| # | HTTP Method | Endpoint Route | Auth Guard | Rate Limit | Primary Purpose |
|:---:|:---:|---|:---:|:---:|---|
| **1** | `POST` | `/api/v1/auth/signup` | Public | Standard | Enrolls existing student from roster (Option 2) |
| **2** | `POST` | `/api/v1/auth/login` | Public | **20 / min** | Authenticates credentials and issues signed JWT |
| **3** | `POST` | `/api/v1/auth/change-password` | Bearer JWT | Standard | Immediately updates password for authenticated student |
| **4** | `GET` | `/api/v1/auth/me` | Bearer JWT | Standard | Validates token and returns verified identity profile |
| **5** | `POST` | `/api/v1/chat` | Bearer JWT | **30 / min** | Multi-turn ReAct agent reasoning turn with dynamic fallback |
| **6** | `GET` | `/api/v1/chat/conversations` | Bearer JWT | Standard | Lists active and historical chat sessions for student |
| **7** | `GET` | `/api/v1/chat/conversations/{conversation_id}/messages` | Bearer JWT | Standard | Chronological message turns and execution metadata |
| **8** | `DELETE` | `/api/v1/chat/conversations/{conversation_id}` | Bearer JWT | Standard | Deletes conversation session and cascading message turns |
| **9** | `GET` | `/api/v1/student/profile` | Bearer JWT | Standard | Retrieves authenticated student demographic profile |
| **10** | `PUT` | `/api/v1/student/profile` | Bearer JWT | Standard | Updates student phone, email, or mailing address |
| **11** | `GET` | `/api/v1/student/fees` | Bearer JWT | Standard | Retrieves tuition ledger, pending balance, and receipts |
| **12** | `GET` | `/api/v1/student/scholarship` | Bearer JWT | Standard | Retrieves active financial grant and renewal criteria |
| **13** | `GET` | `/api/v1/student/tickets` | Bearer JWT | Standard | Retrieves grievance and support escalation tickets |
| **14** | `GET` | `/api/v1/audit/logs` | Public / Internal | Standard | Queries immutable security audit trail with filters |
| **15** | `GET` | `/api/v1/audit/summary` | Public / Internal | Standard | Aggregated compliance metrics for Assignment 2 |
| **16** | `POST` | `/api/v1/ingest` | Public / Internal | Standard | Multipart PDF handbook upload, chunking, and embedding |
| **17** | `GET` | `/health` | Public | None | Deep multi-dependency probe (PostgreSQL, Redis, Qdrant) |

---

## 4. Authentication & Identity (`/api/v1/auth`)

### 4.1 Self-Service Student Enrollment (`POST /api/v1/auth/signup`)

Enrolls an existing university student into portal credentials (**Assignment 2 Option 2**). Pre-validates that the `student_id` exists in the university roster (`students` table).

- **Route**: `POST /api/v1/auth/signup`
- **Auth**: Public
- **Headers**: `Content-Type: application/json`

#### Request Body (`SignupRequest`)
```json
{
  "student_id": "STU006",
  "password": "SecurePassword@123"
}
```

#### Successful Response (`201 Created`)
```json
{
  "status": "success",
  "message": "Account created successfully. You can now log in.",
  "data": {
    "student_id": "STU006",
    "name": "Kavita Reddy",
    "programme": "BBA",
    "batch": "2024-2027"
  }
}
```

#### Error Scenarios
- `400 Bad Request`: Password shorter than 8 characters.
- `404 Not Found`: Student ID is not in university roster (`STU999`).
- `409 Conflict`: Student credentials already registered (`STU001`).

#### Curl Example
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"student_id": "STU006", "password": "SecurePassword@123"}'
```

---

### 4.2 Student Authentication & JWT Login (`POST /api/v1/auth/login`)

Authenticates student credentials via bcrypt hash comparison and issues a signed HS256 JWT access token valid for 24 hours.

- **Route**: `POST /api/v1/auth/login`
- **Auth**: Public
- **Rate Limit**: **20 requests / minute**
- **Headers**: `Content-Type: application/json`

#### Request Body (`LoginRequest`)
```json
{
  "student_id": "STU001",
  "password": "Student@123"
}
```

#### Successful Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Authentication successful.",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

#### Error Scenarios
- `401 Unauthorized`: Invalid credentials or unregistered account.
- `429 Too Many Requests`: Exceeded 20 attempts in 60s.

#### Curl Example
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"student_id": "STU001", "password": "Student@123"}'
```

---

### 4.3 Change Password (`POST /api/v1/auth/change-password`)

Updates the password hash in the database for the authenticated student.

- **Route**: `POST /api/v1/auth/change-password`
- **Auth**: `Bearer <JWT>`
- **Headers**:
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`

#### Request Body (`ChangePasswordRequest`)
```json
{
  "new_password": "NewSecretPassword@456"
}
```

#### Successful Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Password updated successfully.",
  "data": null
}
```

#### Curl Example
```bash
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_password": "NewSecretPassword@456"}'
```

---

### 4.4 Verify Current User Identity (`GET /api/v1/auth/me`)

Validates the incoming JWT bearer token and confirms authenticated student status.

- **Route**: `GET /api/v1/auth/me`
- **Auth**: `Bearer <JWT>`
- **Headers**: `Authorization: Bearer <token>`

#### Successful Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Token is valid.",
  "data": {
    "student_id": "STU001",
    "authenticated": true
  }
}
```

#### Curl Example
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/me
```

---

## 5. Multi-Turn AI Agent Chat (`/api/v1/chat`)

### 5.1 Send Message to AI Agent (`POST /api/v1/chat`)

Executes an interactive **ReAct reasoning loop** turn with two-tier memory, dynamic model fallback (`qwen/qwen3.8-27b`), and sub-second cached RAG policy retrieval.

- **Route**: `POST /api/v1/chat`
- **Auth**: `Bearer <JWT>`
- **Rate Limit**: **30 requests / minute**
- **Headers**:
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`

#### Request Body (`ChatRequest`)
```json
{
  "message": "What is my tuition fee balance, and what is the penalty if I pay late?",
  "conversation_id": "9f8c6e28-48b6-4b48-8df0-184517b6a124"
}
```
*Note: `conversation_id` is optional; omit on the first message to create a new session.*

#### Successful Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Agent response generated successfully.",
  "data": {
    "conversation_id": "9f8c6e28-48b6-4b48-8df0-184517b6a124",
    "message": "Your pending tuition balance is ₹2,25,000 due on October 31, 2026. According to Section 4.2 of the Student Handbook, late fee payments incur a surcharge of ₹500 per day up to 15 days.",
    "role": "assistant",
    "trace_id": "c71a8f90",
    "facts_learned": [
      "inquired_fee_due_date_oct_31"
    ],
    "pending_approval": false,
    "trace": {
      "duration_ms": 185.4,
      "total_tokens": 1240,
      "model": "llama-3.3-70b-versatile",
      "steps": [
        {
          "type": "tool_call",
          "tool_name": "get_fee_status",
          "args": {"student_id": "STU001"}
        },
        {
          "type": "tool_call",
          "tool_name": "search_student_handbook",
          "args": {"query": "late fee payment surcharge penalty"}
        }
      ]
    }
  }
}
```

#### Curl Example
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my fee balance?"}'
```

---

### 5.2 List Student Conversations (`GET /api/v1/chat/conversations`)

Retrieves a summary list of all chat sessions owned by the authenticated student.

- **Route**: `GET /api/v1/chat/conversations`
- **Auth**: `Bearer <JWT>`
- **Headers**: `Authorization: Bearer <token>`

#### Successful Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Retrieved 1 conversations.",
  "data": [
    {
      "id": "9f8c6e28-48b6-4b48-8df0-184517b6a124",
      "student_id": "STU001",
      "title": "Fee Balance & Late Payment Policy",
      "status": "active",
      "created_at": "2026-10-24T10:15:00Z",
      "message_count": 4
    }
  ]
}
```

#### Curl Example
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/chat/conversations
```

---

### 5.3 Get Conversation Turn History (`GET /api/v1/chat/conversations/{conversation_id}/messages`)

Retrieves chronological turns, message roles, and metadata for a specific conversation session.

- **Route**: `GET /api/v1/chat/conversations/{conversation_id}/messages`
- **Auth**: `Bearer <JWT>`
- **Path Parameters**: `conversation_id` (`UUID`, Required)

#### Successful Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Retrieved 2 messages.",
  "data": [
    {
      "id": "b3f0248a-6b45-4e31-8f43-85b4f2c253c1",
      "role": "user",
      "content": "What is my remaining fee balance?",
      "meta_data": null,
      "created_at": "2026-10-24T10:15:00Z"
    },
    {
      "id": "c4d1259b-7c56-5f42-9a54-96c5e3d364d2",
      "role": "assistant",
      "content": "You have ₹2,25,000 due on October 31, 2026.",
      "meta_data": {
        "trace_id": "c71a8f90"
      },
      "created_at": "2026-10-24T10:15:02Z"
    }
  ]
}
```

#### Curl Example
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/chat/conversations/9f8c6e28-48b6-4b48-8df0-184517b6a124/messages
```

---

### 5.4 Delete Conversation Session (`DELETE /api/v1/chat/conversations/{conversation_id}`)

Permanently deletes a chat session and all cascading message turns.

- **Route**: `DELETE /api/v1/chat/conversations/{conversation_id}`
- **Auth**: `Bearer <JWT>`
- **Path Parameters**: `conversation_id` (`UUID`, Required)

#### Successful Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Conversation deleted successfully.",
  "data": {
    "conversation_id": "9f8c6e28-48b6-4b48-8df0-184517b6a124"
  }
}
```

#### Curl Example
```bash
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/chat/conversations/9f8c6e28-48b6-4b48-8df0-184517b6a124
```

---

## 6. Student University Records (`/api/v1/student`)

All student record endpoints enforce **code-level tenant ownership**. A student token can **only** inspect and modify their own records. Cross-student queries return `403 Forbidden` and trigger security audit records.

### 6.1 Get Student Profile (`GET /api/v1/student/profile`)

Returns demographic, academic programme, batch, and contact details for the authenticated student.

- **Route**: `GET /api/v1/student/profile`
- **Auth**: `Bearer <JWT>`

#### Successful Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Student profile retrieved successfully.",
  "data": {
    "student_id": "STU001",
    "name": "Rahul Sharma",
    "programme": "PGDM AI & DS",
    "batch": "2024-2026",
    "status": "active",
    "phone": "+91-9876543210",
    "email": "rahul.sharma@university.edu",
    "address": "42 Tech Park, Whitefield, Bengaluru"
  }
}
```

#### Curl Example
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/student/profile
```

---

### 6.2 Update Student Contact Details (`PUT /api/v1/student/profile`)

Updates phone, email, or mailing address directly in university records. Logs an audit entry.

- **Route**: `PUT /api/v1/student/profile`
- **Auth**: `Bearer <JWT>`
- **Headers**:
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`

#### Request Body (`UpdateProfileRequest`)
```json
{
  "phone": "+91-9988776655",
  "address": "Flat 302, Cyber Heights, Bengaluru"
}
```

#### Successful Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Student profile updated successfully.",
  "data": {
    "student_id": "STU001",
    "name": "Rahul Sharma",
    "programme": "PGDM AI & DS",
    "batch": "2024-2026",
    "status": "active",
    "phone": "+91-9988776655",
    "email": "rahul.sharma@university.edu",
    "address": "Flat 302, Cyber Heights, Bengaluru"
  }
}
```

#### Curl Example
```bash
curl -X PUT http://localhost:8000/api/v1/student/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+91-9988776655", "address": "Flat 302, Cyber Heights, Bengaluru"}'
```

---

### 6.3 Get Tuition Fee Ledger (`GET /api/v1/student/fees`)

Retrieves the authenticated student's financial tuition ledger, total obligations, paid amounts, outstanding balance, due date, and receipt ID.

- **Route**: `GET /api/v1/student/fees`
- **Auth**: `Bearer <JWT>`

#### Successful Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Fee ledger retrieved successfully.",
  "data": {
    "student_id": "STU001",
    "total_fee": 450000.0,
    "paid": 225000.0,
    "pending": 225000.0,
    "due_date": "2026-10-31",
    "status": "partially_paid",
    "receipt": "RCP-2024-001"
  }
}
```

#### Curl Example
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/student/fees
```

---

### 6.4 Get Scholarship Details (`GET /api/v1/student/scholarship`)

Retrieves active scholarship grant, percentage deduction, per-semester award, and renewal status.

- **Route**: `GET /api/v1/student/scholarship`
- **Auth**: `Bearer <JWT>`

#### Successful Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Scholarship details retrieved successfully.",
  "data": {
    "student_id": "STU001",
    "scholarship_type": "Merit Excellence",
    "percentage": 20.0,
    "amount_per_semester": 45000.0,
    "status": "active"
  }
}
```
*Note: If no scholarship is awarded, `data: null` is returned with message `"No active scholarship award on record."`.*

#### Curl Example
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/student/scholarship
```

---

### 6.5 Get Support & Grievance Tickets (`GET /api/v1/student/tickets`)

Retrieves support escalation tickets created by or on behalf of the authenticated student.

- **Route**: `GET /api/v1/student/tickets`
- **Auth**: `Bearer <JWT>`

#### Successful Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Retrieved 1 support tickets.",
  "data": [
    {
      "ticket_id": "TICK-2026-0042",
      "student_id": "STU001",
      "category": "Fee Extension",
      "description": "Request for 15-day installment deferral due to banking delay",
      "priority": "medium",
      "status": "in_progress",
      "created_at": "2026-10-20T14:30:00Z"
    }
  ]
}
```

#### Curl Example
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/student/tickets
```

---

## 7. Security Audit & Compliance (`/api/v1/audit`)

### 7.1 List Security Audit Logs (`GET /api/v1/audit/logs`)

Inspects immutable security trails recorded in PostgreSQL for tool invocations and access control decisions (**Assignment 2 Compliance Requirement**).

- **Route**: `GET /api/v1/audit/logs`
- **Auth**: Public / Internal
- **Query Parameters**:
  - `limit` (`integer`, optional, default `50`, max `200`)
  - `decision` (`string`, optional: `ALLOWED`, `BLOCKED`, `APPROVED`, `REJECTED`)

#### Successful Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Retrieved 2 audit log records.",
  "data": [
    {
      "id": "e4f8d220-4b57-410a-8d19-9f44a80e1234",
      "student_id": "STU001",
      "action": "get_fee_status",
      "target_id": "STU002",
      "decision": "BLOCKED",
      "result": "Access denied: student STU001 cannot query data for student STU002",
      "created_at": "2026-10-24T10:15:01Z"
    },
    {
      "id": "f5a9e331-5c68-421b-9e20-0a55b91f2345",
      "student_id": "STU001",
      "action": "get_fee_status",
      "target_id": "STU001",
      "decision": "ALLOWED",
      "result": "Fee inquiry completed for STU001",
      "created_at": "2026-10-24T10:14:55Z"
    }
  ]
}
```

#### Curl Example
```bash
curl "http://localhost:8000/api/v1/audit/logs?limit=10&decision=BLOCKED"
```

---

### 7.2 Aggregated Compliance Summary (`GET /api/v1/audit/summary`)

Calculates live compliance statistics and decision breakdowns for formal Assignment 2 evaluation.

- **Route**: `GET /api/v1/audit/summary`
- **Auth**: Public / Internal

#### Successful Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Audit summary calculated successfully.",
  "data": {
    "total_events": 142,
    "allowed_count": 118,
    "blocked_count": 14,
    "approved_count": 7,
    "rejected_count": 3,
    "recent_logs": [ ... ]
  }
}
```

#### Curl Example
```bash
curl http://localhost:8000/api/v1/audit/summary
```

---

## 8. Handbook Document Ingestion (`/api/v1/ingest`)

### 8.1 Upload & Vectorize Handbook PDF (`POST /api/v1/ingest`)

Uploads, validates, parses, chunks, and embeds university policy documents into Qdrant vector storage (`student_handbook` collection) and creates an ingestion audit record in PostgreSQL.

- **Route**: `POST /api/v1/ingest`
- **Auth**: Public / Internal
- **Content-Type**: `multipart/form-data`
- **Form Parameters**: `file` (`UploadFile`, PDF document)

#### Successful Response (`201 Created`)
```json
{
  "status": "success",
  "message": "Document 'student_handbook.pdf' successfully parsed, chunked, and embedded into Qdrant.",
  "data": {
    "filename": "student_handbook.pdf",
    "chunks_created": 184,
    "embedding_model": "Orange/orange-nomic-v1.5-1536",
    "vector_collection": "student_handbook"
  }
}
```

#### Error Scenarios
- `400 Bad Request`: File is empty or does not have a `.pdf` extension.

#### Curl Example
```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -F "file=@/path/to/student_handbook.pdf"
```

---

## 9. Deep Health & Diagnostic Probes (`/health`)

### 9.1 Multi-Dependency Deep Probe (`GET /health`)

Executes live, non-blocking asynchronous probes across all core backend dependencies:
1. **PostgreSQL**: Probes connection pool via `SELECT 1`.
2. **Redis**: Pings cache for `PONG` response.
3. **Qdrant**: Checks vector store connectivity via `client.get_collections()`.

- **Route**: `GET /health`
- **Auth**: Public
- **Rate Limit**: None

#### Successful Response (`200 OK` - Healthy)
```json
{
  "status": "healthy",
  "app": "Intelligent Student Support Agent",
  "environment": "development",
  "dependencies": {
    "database": {
      "status": "healthy",
      "type": "postgresql",
      "message": "Connected"
    },
    "cache": {
      "status": "healthy",
      "type": "redis",
      "message": "PONG"
    },
    "vector_db": {
      "status": "healthy",
      "type": "qdrant",
      "message": "Connected"
    }
  }
}
```

#### Degraded Response (`200 OK` - Cache Degraded)
```json
{
  "status": "degraded",
  "app": "Intelligent Student Support Agent",
  "environment": "development",
  "dependencies": {
    "database": {
      "status": "healthy",
      "type": "postgresql",
      "message": "Connected"
    },
    "cache": {
      "status": "degraded",
      "type": "redis",
      "message": "Redis unreachable (in-memory/Postgres fallback)"
    },
    "vector_db": {
      "status": "healthy",
      "type": "qdrant",
      "message": "Connected"
    }
  }
}
```

#### Critical Failure Response (`503 Service Unavailable` - Database Down)
When the primary PostgreSQL database is unreachable, the endpoint returns HTTP status `503 Service Unavailable`.

#### Curl Example
```bash
curl http://localhost:8000/health
```

---

## 10. Student Test Personas Matrix

The PostgreSQL database is pre-seeded with **20 comprehensive student records** (`STU001` through `STU020`) via `just seed`:

| Student ID | Full Name | Programme | Fee Ledger Status | Scholarship | Account Status | Testing Purpose |
|:---:|---|---|---|---|:---:|---|
| **`STU001`** | **Rahul Sharma** | PGDM AI & DS | Partially Paid (₹225k due Oct 31) | 20% Merit (Active) | Pre-Activated (`Student@123`) | Standard fee balance & policy queries |
| **`STU002`** | **Priya Patel** | MBA Marketing | Paid in Full (₹0 due) | None | Pre-Activated (`Student@123`) | Verified paid-in-full queries |
| **`STU003`** | **Amit Verma** | B.Tech CSE | Overdue (₹200k since Sept 1) | 15% Sports (Active) | Pre-Activated (`Student@123`) | Late payment penalty verification |
| **`STU004`** | **Sneha Gupta** | M.Tech Data Science | Unpaid (₹380k due Nov 15) | 25% Research (Active) | Pre-Activated (`Student@123`) | Extension ticket creation testing |
| **`STU005`** | **Vikram Malhotra** | BBA Analytics | Partially Paid (₹150k due Dec 1) | None | Pre-Activated (`Student@123`) | Multi-turn conversational flow |
| **`STU006`**–**`STU020`** | Diverse Cohort | Various | Varied ledgers | Various | **Not Activated** | Available for `POST /signup` testing |
| **`STU999`** | Invalid Student | None | None | None | **Not in Roster** | Negative test (verifies `404 Not Found`) |

---

## 11. End-to-End Curl Testing Guide

Run the following sequential curl commands in your terminal to verify the entire system lifecycle:

```bash
# ==============================================================================
# 1. SYSTEM HEALTH PROBE
# ==============================================================================
curl -s http://localhost:8000/health | jq .

# ==============================================================================
# 2. ENROLL NEW STUDENT (OPTION 2 ENROLLMENT)
# ==============================================================================
curl -s -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"student_id": "STU006", "password": "SecurePassword@123"}' | jq .

# ==============================================================================
# 3. AUTHENTICATE AND OBTAIN JWT ACCESS TOKEN
# ==============================================================================
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"student_id": "STU001", "password": "Student@123"}' | jq -r '.data.access_token')

echo "Acquired Bearer Token: $TOKEN"

# ==============================================================================
# 4. VERIFY AUTHENTICATED IDENTITY
# ==============================================================================
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/me | jq .

# ==============================================================================
# 5. QUERY TUITION FEE LEDGER
# ==============================================================================
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/student/fees | jq .

# ==============================================================================
# 6. ASK AI SUPPORT AGENT (SUB-SECOND RAG RETRIEVAL)
# ==============================================================================
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the minimum attendance requirement for final examinations?"}' | jq .

# ==============================================================================
# 7. CROSS-STUDENT INQUIRY BLOCK TEST (ATTEMPTING TO QUERY STU002 AS STU001)
# ==============================================================================
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Can you check the fee status for student STU002?"}' | jq .

# ==============================================================================
# 8. INSPECT AUDIT LOG FOR THE BLOCKED ATTEMPT
# ==============================================================================
curl -s "http://localhost:8000/api/v1/audit/logs?limit=5&decision=BLOCKED" | jq .

# ==============================================================================
# 9. GET AGGREGATED COMPLIANCE SUMMARY
# ==============================================================================
curl -s http://localhost:8000/api/v1/audit/summary | jq .
```

---

*Documentation maintained by AI Code Review Agent. Interactive documentation is available live at [`http://localhost:8000/docs`](http://localhost:8000/docs).*
