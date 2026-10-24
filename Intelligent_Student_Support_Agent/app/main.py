"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config.database import engine, init_db
from app.config.redis import ping_redis, redis_client
from app.config.settings import settings
from app.exceptions.handlers import register_exception_handlers
from app.routes.index import api_router
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown events."""
    logger.info(f"Starting Intelligent Student Support Agent ({settings.app_env})...")

    # 1. Verify and initialize PostgreSQL Database
    from app.config.database import check_and_initialize_database
    db_type = await check_and_initialize_database()
    logger.info(f"Database operational backend: {db_type}")

    # 2. Verify Redis connection
    if await ping_redis():
        logger.info("Redis cache connection verified successfully.")
    else:
        logger.warning("Redis connection failed. Cache/memory fallback to PostgreSQL.")

    # 3. Pre-warm RAG pipeline (embedding model + Qdrant connection) in background
    from app.tools.rag_tool import warm_rag_pipeline
    asyncio.create_task(warm_rag_pipeline())

    yield  # Application accepts traffic

    # Shutdown
    logger.info("Shutting down application...")
    await redis_client.aclose()
    await engine.dispose()
    logger.info("Database and Redis connections closed cleanly.")


from app.middlewares.security_headers import SecurityHeadersMiddleware
from app.utils.health import check_system_health

# Create FastAPI instance
app = FastAPI(
    title="Intelligent Student Support Agent API",
    version="1.0.0",
    description="Agentic multi-turn support system with memory, RAG, and PostgreSQL audit tracking.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# OWASP Security Headers & Request Correlation ID Middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register global custom exception handlers
register_exception_handlers(app)

# Mount API routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """Service health status endpoint with deep PostgreSQL, Redis, and Qdrant probes."""
    return await check_system_health()


async def _run_cli_loop():
    """Delegates interactive terminal CLI loop to dedicated scripts/cli.py runner."""
    from scripts.cli import run_cli
    await run_cli()


def main():
    """Main CLI entrypoint."""
    import argparse
    import asyncio
    import uvicorn

    parser = argparse.ArgumentParser(description="Intelligent Student Support Agent")
    parser.add_argument("--cli", action="store_true", help="Launch interactive CLI mode")
    parser.add_argument("--host", default=settings.host, help="Bind host for API server")
    parser.add_argument("--port", type=int, default=settings.port, help="Bind port for API server")
    parser.add_argument("--reload", action="store_true", default=True, help="Enable uvicorn hot-reload")

    args = parser.parse_args()

    if args.cli:
        asyncio.run(_run_cli_loop())
    else:
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()

