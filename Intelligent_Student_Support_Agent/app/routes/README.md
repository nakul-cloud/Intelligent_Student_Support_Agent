# 🛣️ Routes Layer (`app/routes`)

The **Routes Layer** defines the RESTful HTTP API contracts, URL path hierarchies, request body schemas, and FastAPI dependency bindings for the application.

---

## 🏗️ Routing & Dependency Injection Flow

```
                     [ Client Request: e.g. GET /api/v1/student/profile ]
                                              │
                                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                  app/routes/index.py                                     │
│                     Aggregates sub-routers under prefix "/api/v1"                        │
└─────────────────────────────────────────────┬────────────────────────────────────────────┘
                                              │
         ┌───────────────────┬────────────────┼────────────────────┬───────────────────┐
         ▼                   ▼                ▼                    ▼                   ▼
┌─────────────────┐ ┌────────────────┐ ┌──────────────┐ ┌──────────────────┐ ┌────────────────┐
│   auth_routes   │ │ student_routes │ │ chat_routes  │ │ ingestion_routes │ │  audit_routes  │
│  /api/v1/auth   │ │/api/v1/student │ │ /api/v1/chat │ │  /api/v1/ingest  │ │ /api/v1/audit  │
└────────┬────────┘ └────────┬───────┘ └──────┬───────┘ └────────┬─────────┘ └────────┬───────┘
         │                   │                │                  │                    │
         └───────────────────┴───────┬────────┴──────────────────┴────────────────────┘
                                     │
                                     ▼
                ┌───────────────────────────────────────────┐
                │        FastAPI Dependency Pipeline        │
                │  - get_current_student (JWT Verification) │
                │  - get_db (AsyncSession Inversion)        │
                └────────────────────┬──────────────────────┘
                                     │ (Forward validated context)
                                     ▼
                        [ Dispatched to Controller ]
```

---

## 📁 Module Inventory

| File | Endpoint Prefix | Tags | Protected | Description |
|---|---|---|:---:|---|
| [`index.py`](./index.py) | `/api/v1` | Root / Health | No | Mounts and aggregates all modular sub-routers under `/api/v1`. |
| [`auth_routes.py`](./auth_routes.py) | `/api/v1/auth` | Authentication | No | Endpoints for self-service enrollment (`POST /signup`) and token issuance (`POST /login`). |
| [`student_routes.py`](./student_routes.py) | `/api/v1/student` | Student Records | **Yes** (JWT) | Access authenticated student records: `/profile` (GET/PUT), `/fees`, `/scholarship`, `/tickets`. |
| [`chat_routes.py`](./chat_routes.py) | `/api/v1/chat` | AI Chat Assistant | **Yes** (JWT) | Multi-turn conversational endpoint (`POST /`), conversation list (`GET /conversations`), and turn history. |
| [`ingestion_routes.py`](./ingestion_routes.py) | `/api/v1/ingest` | Document Ingestion | No | Multipart file upload and asynchronous vector ingestion trigger for student handbooks. |
| [`audit_routes.py`](./audit_routes.py) | `/api/v1/audit` | Audit & Security | No | Query immutable security decision trails and compliance summaries. |

---

## 🔒 Security & Declarative OpenAPI Contracts

- **Declarative Type Safety**: Every route declares Pydantic DTOs for request payloads (`SignupRequest`, `LoginRequest`, `ChatRequest`, `UpdateProfileRequest`).
- **Identity Enforcement**: Protected endpoints declare `Depends(get_current_student)`, which unpacks the Bearer JWT from the `Authorization` header, extracts the `sub` claim, and rejects unauthorized access before reaching controller logic.
- **Swagger Documentation**: Tags and docstrings populate the interactive OpenAPI UI at `http://localhost:8000/docs`.
