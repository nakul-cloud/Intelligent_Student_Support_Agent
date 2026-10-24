# 🛠️ Utilities & Cross-Cutting Concerns (`app/utils`)

The **Utils Layer** provides shared helper modules for ownership security enforcement, password cryptographic hashing, Loguru structured logging, and uniform JSON response formatting.

---

## 🏗️ Cross-Cutting Utility Architecture

```
                                [ Incoming Operations ]
                                           │
         ┌───────────────────┬─────────────┴─────────────┬───────────────────┐
         ▼                   ▼                           ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  ownership.py   │ │   security.py   │ │   response.py   │ │    logger.py    │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ Verifies that   │ │ Bcrypt password │ │ Standardizes    │ │ Loguru rotation │
│ caller identity │ │ hashing and     │ │ JSON API        │ │ & colorized     │
│ owns requested  │ │ secure string   │ │ success / error │ │ console and     │
│ student records.│ │ verification.   │ │ responses.      │ │ file logging.   │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 📁 Module Inventory

| File | Core Component | Role & Functionality |
|---|---|---|
| [`ownership.py`](./ownership.py) | `verify_ownership` | Cross-tenant security guardrail: verifies caller owns the target `student_id` and logs violations to PostgreSQL `audit_logs`. |
| [`security.py`](./security.py) | `hash_password`, `verify_password` | Implements bcrypt password hashing with automatic salt generation and constant-time string verification. |
| [`response.py`](./response.py) | `success_response`, `error_response` | Helper functions producing uniform FastAPI JSON response envelopes (`status`, `message`, `data`/`errors`). |
| [`logger.py`](./logger.py) | `logger` | Configures Loguru with rotating log files (`logs/app.log`), UTC timestamps, and colored console output. |

---

## 🔒 Security Implementation Details

- **Bcrypt Password Security**: Passwords are never stored in plaintext. Hashing utilizes bcrypt with standard work factor salting.
- **Constant-Time Verification**: `bcrypt.checkpw()` guards against timing attacks during password authentication.
- **Fail-Safe Ownership**: If a tool receives mismatched identities, `verify_ownership` raises `AuthorizationError` (HTTP 403) and records a `BLOCKED` decision in PostgreSQL before any database row can be read.
