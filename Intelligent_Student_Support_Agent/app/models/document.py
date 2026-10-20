"""SQLAlchemy model for document uploads and RAG vector ingestion tracking."""

from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.config.constants import DocumentStatus
from app.models.base import BaseModel


class Document(BaseModel):
    """Document table tracking handbook uploads and end-to-end vector indexing status."""

    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str | None] = mapped_column(String, nullable=True)
    file_hash: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_chunks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String,
        default=DocumentStatus.UPLOADED.value,
        index=True,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
