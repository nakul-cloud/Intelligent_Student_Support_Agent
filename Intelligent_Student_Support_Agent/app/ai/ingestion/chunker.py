"""Structure-aware chunking strategy for academic policy documents.

Implements section-based chunking with bounded size (400-600 tokens)
and metadata retention for accurate policy and condition retrieval.
"""

import uuid
from typing import Any, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config.settings import settings
from app.utils.logger import logger


class SectionAwareChunker:
    """Chunks policy sections respecting natural document boundaries and attaching rich provenance metadata."""

    def __init__(
        self,
        target_chunk_chars: Optional[int] = None,
        overlap_chars: Optional[int] = None,
    ) -> None:
        # Load dynamically from environment settings if not explicitly injected
        self.target_chunk_chars = (
            target_chunk_chars if target_chunk_chars is not None else settings.chunk_target_chars
        )
        self.overlap_chars = (
            overlap_chars if overlap_chars is not None else settings.chunk_overlap_chars
        )
        self.fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.target_chunk_chars,
            chunk_overlap=self.overlap_chars,
            separators=["\n\n", ". ", "; ", "\n", " ", ""],
        )
        logger.debug(
            f"Initialized SectionAwareChunker (target_chars={self.target_chunk_chars}, overlap_chars={self.overlap_chars})"
        )

    def chunk_sections(self, sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Split a list of structural sections into retrieval-ready chunks with contextual headers."""
        chunks: list[dict[str, Any]] = []
        global_chunk_idx = 0

        for sec in sections:
            sec_num = sec.get("section_number", "Policy")
            sec_title = sec.get("section_title", "General")
            page_num = sec.get("page_number", 1)
            doc_name = sec.get("source", "student_handbook.pdf")
            text = sec["text"]

            # If section naturally fits within target chunk size, keep it as ONE cohesive chunk!
            if len(text) <= self.target_chunk_chars:
                chunk_id = str(uuid.uuid4())
                contextual_content = (
                    f"[Handbook Section {sec_num}: {sec_title} | Page {page_num}]\n{text}"
                )
                chunks.append({
                    "id": chunk_id,
                    "content": contextual_content,
                    "metadata": {
                        "document_name": doc_name,
                        "section_number": str(sec_num),
                        "section_title": str(sec_title),
                        "page_number": int(page_num),
                        "chunk_index": global_chunk_idx,
                        "is_complete_section": True,
                    },
                })
                global_chunk_idx += 1
            else:
                # If section exceeds target size, split recursively while retaining conditions
                sub_texts = self.fallback_splitter.split_text(text)
                for sub_idx, sub_part in enumerate(sub_texts):
                    chunk_id = str(uuid.uuid4())
                    contextual_content = (
                        f"[Handbook Section {sec_num}: {sec_title} | Page {page_num} (Part {sub_idx+1})]\n{sub_part}"
                    )
                    chunks.append({
                        "id": chunk_id,
                        "content": contextual_content,
                        "metadata": {
                            "document_name": doc_name,
                            "section_number": str(sec_num),
                            "section_title": str(sec_title),
                            "page_number": int(page_num),
                            "chunk_index": global_chunk_idx,
                            "is_complete_section": False,
                            "part": sub_idx + 1,
                        },
                    })
                    global_chunk_idx += 1

        logger.info(
            f"SectionAwareChunker: Produced {len(chunks)} contextual chunks from {len(sections)} sections (target ~{self.target_chunk_chars} chars)."
        )
        return chunks
