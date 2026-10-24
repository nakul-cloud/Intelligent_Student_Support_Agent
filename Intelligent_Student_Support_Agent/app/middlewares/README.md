# 🛡️ Middlewares & Security Guards (`app/middlewares`)

The **Middlewares Layer** provides perimeter security, request correlation, rate limiting, and cryptographic authentication guards for incoming HTTP traffic before requests reach route handlers.

---

## 🏗️ Request Guard & Middleware Pipeline

```mermaid
flowchart TD
    Req["Client HTTP Request<br/>• Method, Path, Headers"] --> SecHeaders["1. SecurityHeadersMiddleware (security_headers.py)<br/>• Extracts / injects UUIDv4 X-Request-ID correlation token<br/>• Sets OWASP headers: nosniff, DENY, strict-origin"]

    SecHeaders --> RateLimiter{"2. rate_limiter Dependency (rate_limiter.py)<br/>Redis sliding-window atomic counter"}

    RateLimiter -- "Threshold Exceeded" --> Err429["Raise 429 Too Many Requests<br/>(Includes X-Request-ID in error body)"]
    RateLimiter -- "Within Limit<br/>Chat: 30/min | Login: 20/min" --> RouteType{"Endpoint Auth Guard"}

    RouteType -- "Public Endpoint<br/>(/signup, /login, /health)" --> Handler["Dispatch to Route Handler"]

    RouteType -- "Protected Endpoint<br/>(Bearer JWT Required)" --> AuthGuard["3. get_current_student (auth.py)<br/>• Extract Bearer token from Authorization header<br/>• Decode HS256 JWT using settings.jwt_secret"]

    AuthGuard --> TokenVerify{"Token Verification"}
    TokenVerify -- "Expired or Invalid Signature" --> Err401["Raise AuthenticationError<br/>(HTTP 401 Unauthorized)"]
    TokenVerify -- "Valid Token" --> InjectUser["Inject validated student_id (sub)<br/>into route parameter"]

    InjectUser --> Handler
```

---

## 📁 Module Inventory

| File | Core Component | Role & Functionality |
|---|---|---|
| [`auth.py`](./auth.py) | `get_current_student` | FastAPI dependency that extracts and validates Bearer JWT tokens, ensures valid `exp` timestamp, and yields the authenticated caller's verified `student_id`. |
| [`security_headers.py`](./security_headers.py) | `SecurityHeadersMiddleware` | Pure ASGI middleware that injects distributed `X-Request-ID` correlation tokens and OWASP security headers (`nosniff`, `DENY`, `strict-origin-when-cross-origin`, `1; mode=block`). |
| [`rate_limiter.py`](./rate_limiter.py) | `rate_limiter` | Sliding-window rate limiter dependency using atomic Redis sorted sets with transparent in-memory window fallback. Protects `/chat` (30/min) and `/auth/login` (20/min). |

---

## 🔒 Security Best Practices

1. **Stateless JWT Claims**: Tokens carry the `sub` (student identifier) and `exp` (expiration), avoiding expensive persistent session lookups in the database for every API call.
2. **Deterministic Tenant Ownership**: Because `get_current_student` extracts the identity directly from the cryptographically signed JWT payload, endpoints cannot be deceived by forged query parameters or path variables.
3. **Defense in Depth**: Every layer operates independently: `SecurityHeadersMiddleware` protects the protocol transport, `rate_limiter` protects system resources, and `get_current_student` guards data authorization.
