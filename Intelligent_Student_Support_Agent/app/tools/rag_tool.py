"""Retrieval-Augmented Generation (RAG) tool for university policies.

This tool enables the conversational AI agent to search the official 44-page
Student Handbook indexed inside the local Qdrant vector database.

Adheres to SOLID principles:
- Single Responsibility (SRP): Exclusively handles vector embedding and policy chunk retrieval.
- Separation of Concerns: Contains only Python execution logic; schemas are decoupled
  in the app/schemas/ layer.
- Dependency Inversion (DIP): Connects to vector store and local embedder abstractions.
"""

from typing import Any, Optional
from app.ai.ingestion.embedder import LocalEmbedder
from app.ai.retrieval.vector_store import QdrantVectorStore
from app.config.settings import settings
from app.utils.logger import logger

# Module-level singletons for efficient reuse across queries
_embedder: Optional[LocalEmbedder] = None
_vector_store: Optional[QdrantVectorStore] = None


def _get_rag_components() -> tuple[LocalEmbedder, QdrantVectorStore]:
    """Lazily initialize and return shared embedding and vector store instances."""
    global _embedder, _vector_store
    if _embedder is None:
        _embedder = LocalEmbedder()
    if _vector_store is None:
        _vector_store = QdrantVectorStore()
    return _embedder, _vector_store


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
    logger.info(
        f"Tool: Searching handbook for '{clean_query}' (section_filter={section_filter}, top_k={effective_top_k})..."
    )

    try:
        embedder, vector_store = _get_rag_components()

        # 1. Convert user question into semantic vector using local nomic embedding model
        query_vector = embedder.embed_query(clean_query)

        # 2. Build metadata filter if a specific section was targeted
        metadata_filters: Optional[dict[str, Any]] = None
        if section_filter and section_filter.strip():
            metadata_filters = {"section_number": section_filter.strip()}

        # 3. Search Qdrant vector collection
        results = vector_store.search(
            query_vector=query_vector,
            top_k=effective_top_k,
            similarity_threshold=settings.similarity_threshold,
            metadata_filters=metadata_filters,
        )

        # 4. Handle no matches gracefully
        if not results:
            logger.info(f"Tool: No handbook matches found above threshold {settings.similarity_threshold}.")
            return (
                f"No specific handbook policies found matching '{clean_query}'. "
                f"Try rephrasing your question or checking related topics like Attendance, Evaluations, or Grading."
            )

        # 5. Format retrieved policy excerpts with clear provenance headers
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

        logger.info(f"Tool: Retrieved {len(results)} handbook citations for '{clean_query}'.")
        return "\n\n---\n\n".join(formatted_excerpts)

    except Exception as exc:
        logger.error(f"Tool: Error searching student handbook: {exc}")
        return f"Error searching the student handbook: {str(exc)}"
