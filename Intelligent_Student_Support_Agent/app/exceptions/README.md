# ⚠️ Exceptions & Error Handling Layer (`app/exceptions`)

The **Exceptions Layer** centralizes domain error modeling, HTTP status translation, and global FastAPI exception handling. It prevents unhandled stack traces from leaking to clients while ensuring standard error response envelopes.

---

## 🏗️ Exception Handling Pipeline

```mermaid
flowchart TD
    Exc["Application Layer Raises Exception<br/>(e.g. ResourceNotFoundError, ValidationError)"] --> Handlers["Global Exception Handlers (handlers.py)"]

    subgraph HandlerTypes["Specialized Exception Handlers"]
        direction TB
        AppErr["app_error_handler<br/>• Intercepts custom AppError hierarchy"]
        HTTPExc["http_exception_handler<br/>• Handles FastAPI / Starlette HTTPException"]
        ValErr["validation_error_handler<br/>• Formats Pydantic v2 RequestValidationError"]
        GlobErr["global_exception_handler<br/>• Catches unexpected unhandled 500 exceptions"]
    end

    Handlers --> AppErr
    Handlers --> HTTPExc
    Handlers --> ValErr
    Handlers --> GlobErr

    AppErr --> Format["Extract request_id from Request State / Header"]
    HTTPExc --> Format
    ValErr --> Format
    GlobErr --> Format

    Format --> Envelope["Uniform Error Envelope<br/>{status: 'fail' | 'error', message, request_id, errors}"]
```

---

## 📁 Module Inventory

| File | Core Component | Description |
|---|---|---|
| [`custom_exceptions.py`](./custom_exceptions.py) | `AppError` Hierarchy | Base domain exception classes with pre-mapped HTTP status codes and user-friendly error messages. |
| [`handlers.py`](./handlers.py) | `register_exception_handlers` | Wires FastAPI exception handlers to format uniform JSON error responses across the entire application lifecycle. |

---

## 📊 Domain Exception Hierarchy

```
AppError (Base Exception, status_code=500)
├── ValidationError (status_code=422)       # Malformed or invalid input payload
├── AuthenticationError (status_code=401)    # Missing/invalid JWT token or bad credentials
├── AuthorizationError (status_code=403)     # Cross-student access or forbidden resource
├── ResourceNotFoundError (status_code=404)  # Student ID not enrolled, record not found
├── ConflictError (status_code=409)          # Duplicate account creation or ticket collision
├── DatabaseError (status_code=500)          # Connection drop or unrecoverable SQL failure
└── ExternalServiceError (status_code=502)   # Groq LLM API or Qdrant vector timeout
```

---

## 💎 Design Standards

- **Informative & Clean Diagnostics**: Every exception carries both a loggable diagnostic string and a clean client message.
- **Fail-Fast**: Enforces hard failures on missing configurations or database disconnects rather than silently degrading into unintended states.
