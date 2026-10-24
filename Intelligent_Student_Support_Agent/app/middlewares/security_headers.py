"""Security headers and Request Correlation ID middleware for FastAPI.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Injects OWASP-recommended security headers and attaches
  traceable X-Request-ID correlation tokens to all inbound/outbound HTTP exchanges.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware attaching OWASP security headers and correlation IDs to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract or generate X-Request-ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        response: Response = await call_next(request)

        # Attach Correlation ID
        response.headers["X-Request-ID"] = request_id

        # Attach OWASP Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response
