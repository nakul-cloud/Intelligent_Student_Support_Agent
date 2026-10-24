"""Qdrant vector store interface with metadata filtering, indexing, and semantic retrieval.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for Qdrant collection management,
  payload indexing, point upserting, and vector search.
- Open/Closed (OCP): Collection name and client configurations are injected from Settings
  or constructor parameters without modifying class logic.
- Dependency Inversion (DIP): Exposes standard vector storage and retrieval methods
  decoupled from upstream RAG ingestion and agent tools.
"""

from typing import Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.config.settings import settings
from app.utils.logger import logger


class QdrantVectorStore:
    """Manages Qdrant collections, vector indexing, payload indexes, and filtered semantic search."""

    def __init__(
        self,
        url: Optional[str] = None,
        collection_name: Optional[str] = None,
    ) -> None:
        """Initialize connection to Qdrant vector store using injected or configured settings."""
        self.url = url or settings.qdrant_url
        self.collection_name = collection_name or settings.qdrant_collection_name
        try:
            client = QdrantClient(url=self.url, timeout=1.5)
            client.get_collections()
            self.client = client
            logger.info(f"Connected to remote Qdrant server at '{self.url}'")
        except Exception as exc:
            logger.warning(
                f"Remote Qdrant at '{self.url}' unavailable ({exc}). Using local embedded Qdrant persistence at './qdrant_storage'..."
            )
            self.client = QdrantClient(path="./qdrant_storage")
        self.dimensions = settings.embedding_dimensions
        self.ensure_collection_exists()

    def ensure_collection_exists(self) -> None:
        """Create Qdrant collection and payload indexes if they do not already exist."""
        try:
            collections_resp = self.client.get_collections()
            existing_names = [col.name for col in collections_resp.collections]

            if self.collection_name not in existing_names:
                logger.info(
                    f"Creating Qdrant collection '{self.collection_name}' (dim={self.dimensions}, metric=Cosine)..."
                )
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.dimensions,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
                logger.info(f"Qdrant collection '{self.collection_name}' created successfully.")

                # Create payload indexes for metadata filtering
                self._create_payload_indexes()
            else:
                logger.debug(f"Qdrant collection '{self.collection_name}' already exists.")
        except Exception as exc:
            logger.error(f"Failed to verify/create Qdrant collection '{self.collection_name}': {exc}")
            raise

    def _create_payload_indexes(self) -> None:
        """Create indexes on payload fields to enable fast metadata filtering."""
        index_fields = [
            ("metadata.section_number", qmodels.PayloadSchemaType.KEYWORD),
            ("metadata.document_name", qmodels.PayloadSchemaType.KEYWORD),
            ("metadata.page_number", qmodels.PayloadSchemaType.INTEGER),
        ]
        for field_name, field_type in index_fields:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_type,
                )
                logger.debug(f"Created payload index for '{field_name}' ({field_type})")
            except Exception as exc:
                logger.warning(f"Payload index creation for '{field_name}' skipped: {exc}")

    def upsert_chunks(self, chunks: list[dict[str, Any]], embeddings: list[list[float]]) -> int:
        """Store chunk vectors and payloads in Qdrant collection."""
        if not chunks or not embeddings:
            return 0

        points = []
        for chunk, vector in zip(chunks, embeddings):
            points.append(
                qmodels.PointStruct(
                    id=chunk["id"],
                    vector=vector,
                    payload={
                        "content": chunk["content"],
                        "metadata": chunk["metadata"],
                    },
                )
            )

        logger.info(f"Upserting {len(points)} points into Qdrant collection '{self.collection_name}'...")
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )
        logger.info(f"Successfully upserted {len(points)} points into Qdrant.")
        return len(points)

    def delete_by_document(self, document_name: str) -> None:
        """Delete all points associated with a specific document name for idempotent ingestion."""
        points_filter = self.build_metadata_filter({"document_name": document_name})
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=points_filter,
            )
            logger.info(f"Deleted old vectors for document '{document_name}' from Qdrant.")
        except Exception as exc:
            logger.warning(f"Failed to delete points by document '{document_name}': {exc}")

    def build_metadata_filter(self, filters: dict[str, Any]) -> qmodels.Filter:
        """Build a Qdrant Filter object from key-value pairs."""
        must_conditions: list[qmodels.FieldCondition] = []
        for key, value in filters.items():
            field_key = key if key.startswith("metadata.") else f"metadata.{key}"
            must_conditions.append(
                qmodels.FieldCondition(
                    key=field_key,
                    match=qmodels.MatchValue(value=value),
                )
            )
        return qmodels.Filter(must=must_conditions)

    def search(
        self,
        query_vector: list[float],
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        metadata_filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Search for top_k relevant chunks with optional metadata filtering and score thresholding."""
        k = top_k or settings.top_k_chunks
        threshold = similarity_threshold or settings.similarity_threshold

        query_filter: Optional[qmodels.Filter] = None
        if metadata_filters:
            query_filter = self.build_metadata_filter(metadata_filters)
            logger.info(f"Applying metadata filter in Qdrant search: {metadata_filters}")

        try:
            if hasattr(self.client, "query_points"):
                response = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    limit=k,
                    score_threshold=threshold,
                    query_filter=query_filter,
                )
                search_results = response.points
            else:
                search_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=k,
                    score_threshold=threshold,
                    query_filter=query_filter,
                )
        except Exception as exc:
            logger.error(f"Qdrant search query failed on collection '{self.collection_name}': {exc}")
            return []

        retrieved: list[dict[str, Any]] = []
        for pt in search_results:
            payload = pt.payload or {}
            retrieved.append({
                "id": str(pt.id),
                "score": round(float(pt.score), 4),
                "content": payload.get("content", ""),
                "metadata": payload.get("metadata", {}),
            })

        logger.info(
            f"Retrieved {len(retrieved)} chunks from Qdrant '{self.collection_name}' (threshold={threshold}, filters={metadata_filters})"
        )
        return retrieved

    def fetch_by_metadata(self, filters: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
        """Scroll collection by exact metadata match without vector query."""
        query_filter = self.build_metadata_filter(filters)
        try:
            records, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            return [
                {
                    "id": str(r.id),
                    "content": (r.payload or {}).get("content", ""),
                    "metadata": (r.payload or {}).get("metadata", {}),
                }
                for r in records
            ]
        except Exception as exc:
            logger.error(f"Failed to fetch by metadata from '{self.collection_name}': {exc}")
            return []
