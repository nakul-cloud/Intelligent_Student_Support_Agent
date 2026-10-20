"""Asynchronous PostgreSQL database connection and session management using SQLAlchemy."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from app.config.settings import settings
from app.models.base import Base
from app.utils.logger import logger

# Create async engine with pool pre-ping to handle stale connections gracefully
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


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
        logger.info("Initializing PostgreSQL schema and creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created successfully.")
