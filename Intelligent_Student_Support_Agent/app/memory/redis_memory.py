"""Redis memory store driver for short-term student fact caching.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for Redis hash reads, writes,
  and TTL management for student session facts.
- Resilient by Design: All operations handle Redis disconnections gracefully,
  returning safe fallbacks (empty dict / None) without interrupting the agent loop.
"""

from typing import Dict, Optional
from redis.asyncio import Redis

from app.config.redis import redis_client
from app.config.settings import settings
from app.utils.logger import logger


class RedisMemoryStore:
    """Manages ephemeral student fact hashes in Redis."""

    def __init__(self, client: Optional[Redis] = None) -> None:
        self.client = client or redis_client
        self.key_prefix = settings.redis_memory_key_prefix
        self.ttl_seconds = settings.redis_memory_ttl_seconds

    def _get_key(self, student_id: str) -> str:
        """Constructs namespaced Redis key for the student."""
        return f"{self.key_prefix}{student_id}"

    async def get_facts(self, student_id: str) -> Dict[str, str]:
        """Retrieves all cached facts for a student from Redis Hash.

        Returns:
            Dictionary of {fact_key: fact_value}, or empty dict on cache miss or Redis error.
        """
        try:
            key = self._get_key(student_id)
            facts = await self.client.hgetall(key)
            return dict(facts) if facts else {}
        except Exception as exc:
            logger.warning(
                f"Redis get_facts failed for {student_id} (falling back to durable store): {exc}"
            )
            return {}

    async def set_fact(self, student_id: str, key: str, value: str) -> None:
        """Stores a single fact in the student's Redis hash and refreshes TTL."""
        try:
            redis_key = self._get_key(student_id)
            await self.client.hset(redis_key, key, value)
            await self.client.expire(redis_key, self.ttl_seconds)
        except Exception as exc:
            logger.warning(
                f"Redis set_fact failed for {student_id}:{key} (will rely on PostgreSQL): {exc}"
            )

    async def set_facts_bulk(self, student_id: str, facts: Dict[str, str]) -> None:
        """Stores multiple facts in bulk into the student's Redis hash and refreshes TTL."""
        if not facts:
            return
        try:
            redis_key = self._get_key(student_id)
            await self.client.hset(redis_key, mapping=facts)
            await self.client.expire(redis_key, self.ttl_seconds)
        except Exception as exc:
            logger.warning(
                f"Redis set_facts_bulk failed for {student_id} (will rely on PostgreSQL): {exc}"
            )

    async def refresh_ttl(self, student_id: str) -> None:
        """Refreshes the rolling TTL for an active student session."""
        try:
            redis_key = self._get_key(student_id)
            await self.client.expire(redis_key, self.ttl_seconds)
        except Exception as exc:
            logger.warning(f"Redis refresh_ttl failed for {student_id}: {exc}")

    async def delete_facts(self, student_id: str) -> None:
        """Purges cached memory for a student."""
        try:
            redis_key = self._get_key(student_id)
            await self.client.delete(redis_key)
        except Exception as exc:
            logger.warning(f"Redis delete_facts failed for {student_id}: {exc}")
