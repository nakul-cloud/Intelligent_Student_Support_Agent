"""Retrieval-Augmented Generation (RAG) tool for university policies.

This tool enables the conversational AI agent to search the official 44-page
Student Handbook indexed inside the local Qdrant vector database.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively handles semantic vector embedding and policy chunk retrieval.
- High Performance:
  1. Multi-tier caching: Redis cache for repeated search queries (sub-2ms response).
  2. Non-blocking asynchronous execution via asyncio.to_thread to keep the event loop responsive.
  3. Pre-warmed singleton instances eliminating cold-start latency.
"""

import asyncio
import hashlib
import time
from typing import Any, Optional

from app.ai.ingestion.embedder import LocalEmbedder
from app.ai.retrieval.vector_store import QdrantVectorStore
from app.config.redis import redis_client
from app.config.settings import settings
from app.utils.logger import logger

# Module-level singletons for efficient reuse across queries
_embedder: Optional[LocalEmbedder] = None
_vector_store: Optional[QdrantVectorStore] = None
_rag_lock = asyncio.Lock()


def _get_rag_components() -> tuple[LocalEmbedder, QdrantVectorStore]:
    """Return shared embedding and vector store instances."""
    global _embedder, _vector_store
    if _embedder is None:
        _embedder = LocalEmbedder()
    if _vector_store is None:
        _vector_store = QdrantVectorStore()
    return _embedder, _vector_store


async def warm_rag_pipeline() -> None:
    """Pre-warm embedding model and Qdrant connections in the background during server boot.

    Eliminates the 10+ second cold-start penalty for student queries.
    """
    try:
        logger.info("RAG Pipeline: Pre-warming embedding model and vector store in background...")
        t0 = time.perf_counter()
        embedder, vector_store = _get_rag_components()
        # Preload weights into memory on background thread
        await asyncio.to_thread(embedder.get_model, settings.embedding_model)
        t_elapsed = time.perf_counter() - t0
        logger.info(f"RAG Pipeline: Pre-warmed successfully in {t_elapsed:.2f}s. Ready for immediate traffic.")
    except Exception as exc:
        logger.warning(f"RAG Pipeline: Background pre-warming encountered an issue: {exc}")


def _build_rag_cache_key(query: str, section_filter: Optional[str], top_k: int) -> str:
    """Generate deterministic cache key for RAG search parameters."""
    raw = f"{query.lower().strip()}:{section_filter or ''}:{top_k}:{settings.similarity_threshold}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"rag:search:{digest}"


async def search_student_handbook(
    query: str,
    section_filter: Optional[str] = None,
    top_k: Optional[int] = None,
) -> str:
    """Search the official Student Handbook for academic policies, rules, and procedures.

    Converts the query into a 1536-dimensional semantic vector and retrieves
    the most relevant policy clauses from Qdrant, with exact page numbers
    and section citations.

    Args:
        query: The natural language search query (e.g. 'minimum attendance for exams',
               'grade dispute process', 'medical leave condonation').
        section_filter: Optional specific section number to restrict search
                        (e.g. '10.2', '10.3', 'Chapter').
        top_k: Number of relevant policy excerpts to retrieve. Defaults to settings.top_k_chunks.

    Returns:
        A formatted string containing numbered policy citations and content text,
        or an informative message if no relevant policies were found.
    """
    clean_query = query.strip()
    if not clean_query:
        return "Search query cannot be empty. Please provide a topic or policy question."

    effective_top_k = top_k if top_k is not None else settings.top_k_chunks
    cache_key = _build_rag_cache_key(clean_query, section_filter, effective_top_k)

    # 1. High-speed Cache Check (Redis L1 cache for RAG results)
    t_start = time.perf_counter()
    try:
        cached_result = await redis_client.get(cache_key)
        if cached_result:
            latency_ms = (time.perf_counter() - t_start) * 1000.0
            logger.info(
                f"Tool: RAG Cache HIT for '{clean_query}' [{latency_ms:.1f}ms] — returning cached citations."
            )
            return cached_result
    except Exception as cache_exc:
        logger.debug(f"Tool: Redis cache probe skipped: {cache_exc}")

    logger.info(
        f"Tool: Searching handbook for '{clean_query}' (section_filter={section_filter}, top_k={effective_top_k})..."
    )

    try:
        embedder, vector_store = _get_rag_components()

        # 2. Convert query to vector non-blockingly using thread pool + in-memory LRU cache
        t_embed_start = time.perf_counter()
        query_vector = await asyncio.to_thread(embedder.embed_query, clean_query)
        embed_ms = (time.perf_counter() - t_embed_start) * 1000.0

        # 3. Build metadata filter if a specific section was targeted
        metadata_filters: Optional[dict[str, Any]] = None
        if section_filter and section_filter.strip():
            metadata_filters = {"section_number": section_filter.strip()}

        # 4. Search Qdrant vector collection non-blockingly
        t_search_start = time.perf_counter()
        results = await asyncio.to_thread(
            vector_store.search,
            query_vector=query_vector,
            top_k=effective_top_k,
            similarity_threshold=settings.similarity_threshold,
            metadata_filters=metadata_filters,
        )
        search_ms = (time.perf_counter() - t_search_start) * 1000.0

        # 5. Handle no matches gracefully
        if not results:
            logger.info(
                f"Tool: No handbook matches found above threshold {settings.similarity_threshold} "
                f"[embed: {embed_ms:.1f}ms, search: {search_ms:.1f}ms]."
            )
            return (
                f"No specific handbook policies found matching '{clean_query}'. "
                f"Try rephrasing your question or checking related topics like Attendance, Evaluations, or Grading."
            )

        # 6. Format retrieved policy excerpts with clear provenance headers
        formatted_excerpts = []
        for idx, item in enumerate(results, start=1):
            meta = item.get("metadata", {})
            sec_num = meta.get("section_number", "General")
            sec_title = meta.get("section_title", "Handbook Policy")
            page_num = meta.get("page_number", "N/A")
            similarity_score = item.get("score", 0.0)

            raw_content = item.get("content", "").strip()

            header = (
                f"[Citation #{idx} | Handbook Section {sec_num}: {sec_title} | "
                f"Page {page_num} | Relevance: {similarity_score:.2f}]"
            )
            formatted_excerpts.append(f"{header}\n{raw_content}")

        total_ms = (time.perf_counter() - t_start) * 1000.0
        output_text = "\n\n---\n\n".join(formatted_excerpts)
        logger.info(
            f"Tool: Retrieved {len(results)} handbook citations for '{clean_query}' in {total_ms:.1f}ms "
            f"(embed: {embed_ms:.1f}ms, vector_search: {search_ms:.1f}ms)."
        )

        # 7. Store result in Redis cache with 24-hour TTL (86400s)
        try:
            await redis_client.set(cache_key, output_text, ex=86400)
        except Exception as cache_write_exc:
            logger.debug(f"Tool: Failed to cache RAG result in Redis: {cache_write_exc}")

        return output_text

    except Exception as exc:
        logger.error(f"Tool: Error during handbook policy retrieval: {exc}")
        return f"Unable to retrieve handbook policies due to an internal search error: {str(exc)}"
