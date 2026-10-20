"""Structure-aware PDF parser tailored for university student handbooks.

Preserves numbered policy sections, chapter boundaries, bulleted rules,
and page numbers according to production RAG best practices.
"""

import io
import re
from typing import Any, Optional
import pymupdf
from app.utils.logger import logger

# Regex to match numbered sections like "10.2 Eligibility for Writing End-Term Examination" or "1. Introduction"
SECTION_HEADING_REGEX = re.compile(r"^(\d+(?:\.\d+)*)\s+([A-Za-z].*)$")

# Regex to match top-level unnumbered chapters / annexures
CHAPTER_HEADING_REGEX = re.compile(
    r"^(Introduction|Vision|Mission|Programme Structure|Evaluation System|Annexure\s+[A-Z0-9]+|Table of Contents)",
    re.IGNORECASE,
)


class StructureAwarePDFParser:
    """Extracts text while identifying document structural boundaries (sections and page provenance)."""

    def parse_file(self, file_path: str) -> list[dict[str, Any]]:
        """Parse PDF from disk path."""
        logger.info(f"StructureAwarePDFParser: Loading PDF from '{file_path}'")
        doc = pymupdf.open(file_path)
        filename = file_path.replace("\\", "/").split("/")[-1]
        return self._extract_structured_sections(doc, filename)

    def parse_bytes(self, file_bytes: bytes, filename: str = "document.pdf") -> list[dict[str, Any]]:
        """Parse PDF from in-memory bytes."""
        logger.info(f"StructureAwarePDFParser: Loading {len(file_bytes)} bytes for '{filename}'")
        stream = io.BytesIO(file_bytes)
        doc = pymupdf.open(stream=stream, filetype="pdf")
        return self._extract_structured_sections(doc, filename)

    def _extract_structured_sections(self, doc: pymupdf.Document, source_name: str) -> list[dict[str, Any]]:
        """Extract sections grouped by structural headings across all pages."""
        sections: list[dict[str, Any]] = []
        total_pages = len(doc)
        logger.info(f"Parsing {total_pages} pages for structured sections...")

        current_sec_num: str = "0.0"
        current_sec_title: str = "General Handbook Overview"
        current_page: int = 1
        current_text_buffer: list[str] = []

        def flush_section():
            nonlocal current_text_buffer
            raw_text = "\n".join(current_text_buffer).strip()
            # Filter out Table of Contents and empty sections
            if raw_text and len(raw_text) > 40 and "Table of Contents" not in current_sec_title:
                sections.append({
                    "source": source_name,
                    "section_number": current_sec_num,
                    "section_title": current_sec_title,
                    "page_number": current_page,
                    "text": raw_text,
                })
            current_text_buffer = []

        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc[page_idx]
            page_text = page.get_text("text")

            if not page_text or not page_text.strip():
                continue

            lines = page_text.split("\n")

            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue

                # Ignore page footer/header markers like "Page | 6"
                if re.match(r"^Page\s*\|\s*[IVXLCDM0-9]+", line_stripped, re.IGNORECASE):
                    continue

                # Check if this line is a numbered section heading
                m_num = SECTION_HEADING_REGEX.match(line_stripped)
                m_chap = CHAPTER_HEADING_REGEX.match(line_stripped)

                if m_num and len(line_stripped) < 90:
                    flush_section()
                    current_sec_num = m_num.group(1)
                    current_sec_title = m_num.group(2).strip()
                    current_page = page_num
                    current_text_buffer.append(line_stripped)
                elif m_chap and len(line_stripped) < 70:
                    flush_section()
                    current_sec_num = "Chapter"
                    current_sec_title = line_stripped
                    current_page = page_num
                    current_text_buffer.append(line_stripped)
                else:
                    current_text_buffer.append(line_stripped)

        # Flush final section
        flush_section()
        doc.close()

        logger.info(
            f"Successfully extracted {len(sections)} structural policy sections from {total_pages} pages."
        )
        return sections
