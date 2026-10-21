"""Qdrant vector store interface with metadata filtering, indexing, and semantic retrieval.

Supports cosine similarity search with exact metadata filters (section_number, page_number, document_name).
"""

from typing import Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.config.settings import settings
from app.utils.logger import logger


class QdrantVectorStore:
    """Manages Qdrant collections, vector indexing, payload indexes, and filtered semantic search."""

    COLLECTION_NAME = "student_handbook"

    def __init__(self, url: Optional[str] = None) -> None:
        self.url = url or settings.qdrant_url
        self.client = QdrantClient(url=self.url)
        self.dimensions = settings.embedding_dimensions
        self.ensure_collection_exists()

    def ensure_collection_exists(self) -> None:
        """Create Qdrant collection and payload indexes if they do not already exist."""
        try:
            collections_resp = self.client.get_collections()
            existing_names = [col.name for col in collections_resp.collections]

            if self.COLLECTION_NAME not in existing_names:
                logger.info(
                    f"Creating Qdrant collection '{self.COLLECTION_NAME}' (dim={self.dimensions}, metric=Cosine)..."
                )
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=qmodels.VectorParams(
                        size=self.dimensions,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
                logger.info(f"Qdrant collection '{self.COLLECTION_NAME}' created successfully.")

                # Create payload indexes for metadata filtering
                self._create_payload_indexes()
            else:
                logger.debug(f"Qdrant collection '{self.COLLECTION_NAME}' already exists.")
        except Exception as exc:
            logger.error(f"Failed to verify/create Qdrant collection: {exc}")
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
                    collection_name=self.COLLECTION_NAME,
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

        logger.info(f"Upserting {len(points)} points into Qdrant collection '{self.COLLECTION_NAME}'...")
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points,
            wait=True,
        )
        logger.info(f"Successfully upserted {len(points)} points into Qdrant.")
        return len(points)

    def delete_by_document(self, document_name: str) -> None:
        """Delete all points associated with a specific document name for idempotent ingestion."""
        try:
            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="metadata.document_name",
                            match=qmodels.MatchValue(value=document_name),
                        )
                    ]
                ),
            )
            logger.info(f"Cleared existing points for document '{document_name}' from Qdrant.")
        except Exception as exc:
            logger.warning(f"Could not delete previous points for document '{document_name}': {exc}")


    def build_metadata_filter(self, filters: dict[str, Any]) -> qmodels.Filter:
        """Build a Qdrant Filter object from key-value pairs.
        
        Example:
            filters = {"section_number": "10.2", "page_number": 9}
            -> Filter(must=[FieldCondition(key="metadata.section_number", match=MatchValue("10.2")), ...])
        """
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
                    collection_name=self.COLLECTION_NAME,
                    query=query_vector,
                    limit=k,
                    score_threshold=threshold,
                    query_filter=query_filter,
                )
                search_results = response.points
            else:
                search_results = self.client.search(
                    collection_name=self.COLLECTION_NAME,
                    query_vector=query_vector,
                    limit=k,
                    score_threshold=threshold,
                    query_filter=query_filter,
                )
        except Exception as exc:
            logger.error(f"Qdrant search query failed: {exc}")
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
            f"Retrieved {len(retrieved)} chunks from Qdrant (threshold={threshold}, filters={metadata_filters})"
        )
        return retrieved

    def fetch_by_metadata(self, filters: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
        """Scroll collection by exact metadata match without vector query."""
        query_filter = self.build_metadata_filter(filters)
        try:
            records, _ = self.client.scroll(
                collection_name=self.COLLECTION_NAME,
                scroll_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            return [
                {"id": str(r.id), "content": (r.payload or {}).get("content", ""), "metadata": (r.payload or {}).get("metadata", {})}
                for r in records
            ]
        except Exception as exc:
            logger.error(f"Failed to fetch by metadata: {exc}")
            return []

    def delete_by_document(self, document_name: str) -> None:
        """Delete all points associated with a specific document name."""
        points_filter = self.build_metadata_filter({"document_name": document_name})
        try:
            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=points_filter,
            )
            logger.info(f"Deleted old vectors for document '{document_name}' from Qdrant.")
        except Exception as exc:
            logger.warning(f"Failed to delete points by document '{document_name}': {exc}")
