"""Document ingestion service orchestrating parsing, chunking, embedding, vector store upsert, and PostgreSQL tracking."""

import hashlib
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy import select
from app.ai.ingestion.chunker import SectionAwareChunker
from app.ai.ingestion.embedder import LocalEmbedder
from app.ai.ingestion.pdf_parser import StructureAwarePDFParser
from app.ai.retrieval.vector_store import QdrantVectorStore
from app.config.constants import DocumentStatus
from app.config.database import AsyncSessionLocal
from app.models.document import Document
from app.utils.logger import logger


class IngestionService:
    """Service orchestrating end-to-end document indexing and PostgreSQL audit tracking."""

    def __init__(self) -> None:
        self.parser = StructureAwarePDFParser()
        self.chunker = SectionAwareChunker()
        self.embedder = LocalEmbedder()
        self.vector_store = QdrantVectorStore()

    async def ingest_file(self, file_path: str) -> dict[str, Any]:
        """Ingest a PDF from filesystem path and track lifecycle in PostgreSQL."""
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        filename = file_path.replace("\\", "/").split("/")[-1]
        return await self.ingest_bytes(file_bytes, filename=filename, file_path=file_path)

    async def ingest_bytes(
        self,
        file_bytes: bytes,
        filename: str,
        file_path: Optional[str] = None,
    ) -> dict[str, Any]:
        """Ingest raw PDF bytes and log each stage in PostgreSQL documents table."""
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        file_size = len(file_bytes)
        logger.info(f"Starting ingestion for '{filename}' ({file_size} bytes, SHA-256: {file_hash[:10]}...)")

        doc_record: Optional[Document] = None

        async with AsyncSessionLocal() as session:
            # 1. Register or find document in PostgreSQL
            res = await session.execute(select(Document).where(Document.file_hash == file_hash))
            doc_record = res.scalar_one_or_none()

            if not doc_record:
                doc_record = Document(
                    filename=filename,
                    file_path=file_path,
                    file_hash=file_hash,
                    file_size_bytes=file_size,
                    status=DocumentStatus.UPLOADED.value,
                )
                session.add(doc_record)
            else:
                doc_record.status = DocumentStatus.UPLOADED.value
                doc_record.error_message = None

            await session.commit()
            await session.refresh(doc_record)
            doc_id = doc_record.id

        try:
            # 2. Parsing stage
            await self._update_doc_status(doc_id, DocumentStatus.PROCESSING.value)
            sections = self.parser.parse_bytes(file_bytes, filename=filename)
            total_pages = max([s["page_number"] for s in sections], default=len(sections))

            # 3. Chunking stage
            chunks = self.chunker.chunk_sections(sections)
            total_chunks = len(chunks)

            # Update page and chunk counts
            async with AsyncSessionLocal() as session:
                doc = await session.get(Document, doc_id)
                if doc:
                    doc.total_pages = total_pages
                    doc.total_chunks = total_chunks
                    await session.commit()

            # 4. Embedding stage
            await self._update_doc_status(doc_id, DocumentStatus.EMBEDDED.value)
            chunk_texts = [c["content"] for c in chunks]
            embeddings = self.embedder.embed_documents(chunk_texts)

            # 5. Qdrant vector store upsert stage
            upserted_count = self.vector_store.upsert_chunks(chunks, embeddings)

            # 6. Mark as successfully inserted in PostgreSQL
            async with AsyncSessionLocal() as session:
                doc = await session.get(Document, doc_id)
                if doc:
                    doc.status = DocumentStatus.INSERTED.value
                    doc.completed_at = datetime.now(timezone.utc)
                    await session.commit()

            logger.info(
                f"Ingestion completed for '{filename}': {total_pages} pages, {total_chunks} chunks inserted into Qdrant & tracked in PostgreSQL."
            )
            return {
                "document_id": str(doc_id),
                "filename": filename,
                "file_hash": file_hash,
                "total_pages": total_pages,
                "total_chunks": total_chunks,
                "status": DocumentStatus.INSERTED.value,
            }

        except Exception as exc:
            logger.error(f"Ingestion failed for '{filename}': {exc}")
            async with AsyncSessionLocal() as session:
                doc = await session.get(Document, doc_id)
                if doc:
                    doc.status = DocumentStatus.FAILED.value
                    doc.error_message = str(exc)
                    await session.commit()
            raise

    async def _update_doc_status(self, doc_id: Any, status: str) -> None:
        """Helper to update document status in PostgreSQL."""
        async with AsyncSessionLocal() as session:
            doc = await session.get(Document, doc_id)
            if doc:
                doc.status = status
                await session.commit()
