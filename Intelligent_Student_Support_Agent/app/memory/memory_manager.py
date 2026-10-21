"""Memory manager orchestrating two-tier memory (Redis + PostgreSQL) and privacy filtering.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Acts as the unified facade orchestrating Redis cache,
  PostgreSQL durable storage, hybrid regex fact extraction, and privacy classification.
- Open/Closed (OCP): Fact patterns and sensitive keyword definitions are dynamically
  configured and extensible without breaking storage layers.
- Dependency Inversion (DIP): Injects RedisMemoryStore, PostgresMemoryStore, and session.
"""

import re
from typing import Dict, List, Literal, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.memory.postgres_memory import PostgresMemoryStore
from app.memory.redis_memory import RedisMemoryStore
from app.schemas.memory_schema import ExtractedFact, MemoryContextSchema
from app.utils.logger import logger


# Hybrid regex slot patterns for deterministic, zero-token fact extraction
DEFAULT_SLOT_PATTERNS: List[Tuple[str, re.Pattern]] = [
    (
        "programme",
        re.compile(
            r"(?:studying|enrolled in|pursuing)\s+([A-Za-z0-9\s&]+?)(?=[,\.\n]|\bin the\b|\bbatch\b|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "batch",
        re.compile(
            r"(?:batch\s+)?(\d{4}[-–]\d{2,4})(?:\s+batch)?",
            re.IGNORECASE,
        ),
    ),
    (
        "preferred_name",
        re.compile(
            r"(?:call me|my name is)\s+([A-Z][a-z]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "academic_goal",
        re.compile(
            r"(?:interested in|aiming to|want to specialize in|goal is)\s+([A-Za-z0-9\s]+?)(?=[,\.\n]|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "known_issue",
        re.compile(
            r"(?:issue with|problem with|facing problem in)\s+([A-Za-z0-9\s]+?)(?=[,\.\n]|$)",
            re.IGNORECASE,
        ),
    ),
]


class MemoryManager:
    """Facade orchestrating the two-tier memory system with privacy scrubbing."""

    def __init__(
        self,
        session: AsyncSession,
        redis_store: Optional[RedisMemoryStore] = None,
        postgres_store: Optional[PostgresMemoryStore] = None,
    ) -> None:
        self.session = session
        self.redis_store = redis_store or RedisMemoryStore()
        self.postgres_store = postgres_store or PostgresMemoryStore(session)
        self.sensitive_keywords = settings.sensitive_keywords
        self.slot_patterns = DEFAULT_SLOT_PATTERNS

    def classify_sensitivity(self, text: str) -> Literal["store", "skip"]:
        """Evaluates text against security keywords to prevent storing sensitive data.

        Returns:
            'skip' if text contains sensitive data (e.g. otp, password, cvv, pin).
            'store' if clean.
        """
        if not text:
            return "skip"

        lowered = text.lower()
        for keyword in self.sensitive_keywords:
            pattern = re.escape(keyword).replace("_", r"[\s_]")
            if re.search(rf"\b{pattern}\b", lowered):
                logger.warning(
                    f"Privacy Guard: Sensitive keyword '{keyword}' detected. Skipping persistence."
                )
                return "skip"

        return "store"

    def extract_facts(self, conversation_text: str) -> List[ExtractedFact]:
        """Hybrid deterministic extraction of user profile facts from conversation text.

        Saves LLM tokens by using regex slot-matching rather than expensive LLM passes.
        """
        extracted: List[ExtractedFact] = []
        seen_keys = set()

        for slot_key, pattern in self.slot_patterns:
            match = pattern.search(conversation_text)
            if match and slot_key not in seen_keys:
                value = match.group(1).strip()
                # Filter out single-letter or invalid captures
                if len(value) >= 2 and len(value) <= 100:
                    extracted.append(ExtractedFact(fact_key=slot_key, fact_value=value))
                    seen_keys.add(slot_key)

        return extracted

    async def load_memory(self, student_id: str) -> str:
        """Loads memory for a student session, optimizing for latency and accuracy.

        Strategy:
        1. Query Redis Hash cache (Tier 1).
        2. On cache hit -> format and return prompt string.
        3. On cache miss -> query PostgreSQL durable store (Tier 2).
        4. If PostgreSQL has facts -> backfill Redis cache (warm up) -> format and return.
        5. If empty -> return default notice.
        """
        # Tier 1: Check Redis cache
        cached_facts = await self.redis_store.get_facts(student_id)
        if cached_facts:
            facts = [
                ExtractedFact(fact_key=k, fact_value=v)
                for k, v in cached_facts.items()
            ]
            logger.debug(f"MemoryManager cache HIT (Redis) for student: {student_id}")
            return MemoryContextSchema(student_id=student_id, facts=facts).format_for_prompt()

        # Tier 2: Check PostgreSQL durable store
        pg_facts_dict = await self.postgres_store.get_facts_dict(student_id)
        if pg_facts_dict:
            # Warm up Redis cache for subsequent turns
            await self.redis_store.set_facts_bulk(student_id, pg_facts_dict)
            facts = [
                ExtractedFact(fact_key=k, fact_value=v)
                for k, v in pg_facts_dict.items()
            ]
            logger.debug(f"MemoryManager cache MISS (PostgreSQL loaded & Redis warmed) for {student_id}")
            return MemoryContextSchema(student_id=student_id, facts=facts).format_for_prompt()

        return "No prior memory recorded for this student."

    async def save_memory(
        self, student_id: str, conversation_text: str
    ) -> List[ExtractedFact]:
        """Extracts candidate facts, classifies for privacy, and persists safe facts.

        Returns:
            List of facts that passed privacy classification and were stored.
        """
        candidate_facts = self.extract_facts(conversation_text)
        saved_facts: List[ExtractedFact] = []
        safe_dict: Dict[str, str] = {}

        for fact in candidate_facts:
            # Enforce privacy check on both key and value
            if self.classify_sensitivity(fact.fact_value) == "skip" or self.classify_sensitivity(fact.fact_key) == "skip":
                logger.info(
                    f"Privacy Guard: Fact '{fact.fact_key}' rejected due to sensitive contents."
                )
                continue

            safe_dict[fact.fact_key] = fact.fact_value
            saved_facts.append(fact)

        if safe_dict:
            # Persist to Redis short-term cache
            await self.redis_store.set_facts_bulk(student_id, safe_dict)
            # Persist to PostgreSQL durable store
            await self.postgres_store.upsert_facts_bulk(student_id, safe_dict)
            logger.info(f"Persisted {len(safe_dict)} facts to memory tiers for student {student_id}")

        return saved_facts
