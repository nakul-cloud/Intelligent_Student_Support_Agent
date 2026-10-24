"""Asynchronous database connection and session management using SQLAlchemy and PostgreSQL.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively manages PostgreSQL async engine, sessions, and table initialization.
- Dependency Inversion (DIP): Injects AsyncSession into repositories and services.
"""

from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.config.settings import settings
from app.models.base import Base
from app.utils.logger import logger

# Primary PostgreSQL Engine initialization with production pool tuning
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def check_and_initialize_database() -> str:
    """Verifies PostgreSQL connectivity and ensures all schema tables are initialized.

    Raises:
        RuntimeError: If PostgreSQL connection fails. Fail-fast with clear diagnostics.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL database connection verified successfully.")

        # Ensure all registered tables exist in PostgreSQL
        await init_db()
        return "postgresql"
    except Exception as exc:
        logger.critical(
            f"Failed to connect to PostgreSQL at {settings.database_url}: {exc}. "
            "Please ensure the PostgreSQL Docker container is running (e.g., 'just up')."
        )
        raise RuntimeError(
            f"PostgreSQL connection failure: {exc}. Ensure docker compose is running."
        ) from exc


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as exc:
            await session.rollback()
            logger.error(f"Database session rollback due to error: {exc}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all registered database tables in PostgreSQL."""
    async with engine.begin() as conn:
        logger.info("Verifying PostgreSQL schema and registering tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("PostgreSQL database tables verified/created successfully.")
