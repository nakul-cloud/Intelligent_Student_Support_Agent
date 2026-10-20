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

    # 1. Verify PostgreSQL connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL connection verified successfully.")
    except Exception as exc:
        logger.critical(f"PostgreSQL connection failed: {exc}")
        raise

    # 2. Verify Redis connection
    if await ping_redis():
        logger.info("Redis cache connection verified successfully.")
    else:
        logger.warning("Redis connection failed. Cache/memory fallback to PostgreSQL.")

    yield  # Application accepts traffic

    # Shutdown
    logger.info("Shutting down application...")
    await redis_client.aclose()
    await engine.dispose()
    logger.info("Database and Redis connections closed cleanly.")


# Create FastAPI instance
app = FastAPI(
    title="Intelligent Student Support Agent API",
    version="1.0.0",
    description="Agentic multi-turn support system with memory, RAG, and PostgreSQL audit tracking.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    """Service health status endpoint."""
    return {"status": "ok", "app": "Intelligent Student Support Agent", "environment": settings.app_env}
