"""Script to initialize all database tables in PostgreSQL."""

import asyncio
from app.config.database import engine
from app.models import Base
from app.utils.logger import logger


async def init_tables() -> None:
    """Create all registered database tables in PostgreSQL."""
    logger.info("Connecting to PostgreSQL and creating all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("All tables (conversations, messages, student_memory, documents, students, fee_records, scholarships, support_tickets) created successfully!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_tables())
