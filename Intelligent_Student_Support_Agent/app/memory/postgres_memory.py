"""PostgreSQL durable store repository for student memory facts.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively manages durable persistence, retrieval,
  and idempotent upserts for the student_memory table.
- Dependency Inversion (DIP): Injects AsyncSession for transactional operations.
"""

from typing import Dict, List
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student_memory import StudentMemory
from app.utils.logger import logger


class PostgresMemoryStore:
    """Manages long-term durable student facts in PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_facts(self, student_id: str) -> List[StudentMemory]:
        """Retrieves all stored facts for a student from the durable store."""
        stmt = (
            select(StudentMemory)
            .where(StudentMemory.student_id == student_id)
            .order_by(StudentMemory.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_facts_dict(self, student_id: str) -> Dict[str, str]:
        """Retrieves all facts as a key-value dictionary for fast lookup."""
        records = await self.get_facts(student_id)
        return {record.fact_key: record.fact_value for record in records}

    async def upsert_fact(self, student_id: str, fact_key: str, fact_value: str) -> None:
        """Idempotently inserts or updates a single durable student fact."""
        stmt = (
            pg_insert(StudentMemory)
            .values(
                student_id=student_id,
                fact_key=fact_key,
                fact_value=fact_value,
            )
            .on_conflict_do_update(
                constraint="uq_student_memory_fact",
                set_={"fact_value": fact_value},
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
        logger.debug(f"Upserted memory fact for {student_id}: {fact_key}={fact_value}")

    async def upsert_facts_bulk(self, student_id: str, facts: Dict[str, str]) -> None:
        """Idempotently upserts multiple facts for a student in a single transaction."""
        if not facts:
            return

        for key, value in facts.items():
            stmt = (
                pg_insert(StudentMemory)
                .values(
                    student_id=student_id,
                    fact_key=key,
                    fact_value=value,
                )
                .on_conflict_do_update(
                    constraint="uq_student_memory_fact",
                    set_={"fact_value": value},
                )
            )
            await self.session.execute(stmt)

        await self.session.commit()
        logger.info(f"Upserted {len(facts)} memory facts into PostgreSQL for {student_id}")

    async def delete_facts(self, student_id: str) -> None:
        """Deletes all durable memory facts for a student."""
        stmt = delete(StudentMemory).where(StudentMemory.student_id == student_id)
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Purged durable memory facts for {student_id}")
