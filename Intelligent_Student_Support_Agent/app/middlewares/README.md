# 🛡️ Middlewares & Authentication Guards (`app/middlewares`)

The **Middlewares Layer** provides boundary security, identity extraction, and dependency injection guards for protected HTTP routes.

---

## 🏗️ Bearer Authentication Flow

```
[ Incoming Client Request ]
  Headers: { "Authorization": "Bearer eyJhbGciOi..." }
             │
             ▼
┌──────────────────────────────────────────────────────────┐
│             HTTPBearer Security Scheme Dependency        │
│              (FastAPI HTTPBearer / auto_error=True)      │
└────────────────────────────┬─────────────────────────────┘
                             │ (Extracts Raw Token String)
                             ▼
┌──────────────────────────────────────────────────────────┐
│      get_current_student(credentials: HTTPAuthorization) │
│                (app/middlewares/auth.py)                 │
├──────────────────────────────────────────────────────────┤
│ 1. Unpacks token string from Bearer schema               │
│ 2. Decodes JWT using settings.jwt_secret & algorithm     │
│ 3. Validates expiration claim ('exp') against UTC now    │
│ 4. Extracts student identity claim ('sub')               │
└────────────────────────────┬─────────────────────────────┘
                             │
            ┌────────────────┴────────────────┐
            │ (Valid Token)                   │ (Invalid / Expired)
            ▼                                 ▼
┌────────────────────────────┐    ┌──────────────────────────────┐
│ Injects validated          │    │ Raises AuthenticationError   │
│ `student_id: str` into     │    │ (HTTP 401 Unauthorized)      │
│ endpoint parameter         │    └──────────────────────────────┘
└────────────────────────────┘
```

---

## 📁 Module Inventory

| File | Core Component | Role & Functionality |
|---|---|---|
| [`auth.py`](./auth.py) | `get_current_student` | FastAPI dependency function that validates Bearer JWT tokens and yields the authenticated caller's verified `student_id`. |

---

## 🔒 Security Best Practices

1. **Stateless JWT Claims**: Tokens carry the `sub` (student identifier) and `exp` (expiration), avoiding persistent session lookups in memory for every API touchpoint.
2. **Deterministic Ownership**: Because `get_current_student` extracts the ID directly from the cryptographically signed JWT payload, endpoints cannot be tricked by forged query parameters or path variables.
3. **Consistent Rejection**: Missing headers, malformed signatures, or expired tokens immediately trigger an `AuthenticationError` (status 401).
