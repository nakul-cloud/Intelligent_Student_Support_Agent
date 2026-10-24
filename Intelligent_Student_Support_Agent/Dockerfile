# ==============================================================================
# Multi-Stage Production Dockerfile for Intelligent Student Support Agent
# ==============================================================================

# Stage 1: Build & Dependency Synchronization
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binary for rapid dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project manifests
COPY pyproject.toml uv.lock ./

# Install production dependencies into virtual environment
RUN uv sync --frozen --no-dev --no-install-project


# Stage 2: Minimal Production Runtime
FROM python:3.12-slim AS runner

WORKDIR /app

# Configure Python runtime flags
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    APP_ENV=production

# Install curl for container health check probes
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application source code & required assets
COPY app/ ./app/
COPY data/ ./data/
COPY tracing/ ./tracing/
COPY scripts/ ./scripts/
COPY pyproject.toml ./

# Enforce non-root execution for security hardening
RUN addgroup --system appgroup && adduser --system --group appuser \
    && mkdir -p logs traces \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Native Docker health check probe using deep /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start production ASGI uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
