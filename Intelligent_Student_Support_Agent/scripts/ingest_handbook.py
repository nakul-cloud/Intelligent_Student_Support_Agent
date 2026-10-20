"""CLI script to ingest the university student handbook PDF into Qdrant & PostgreSQL."""

import asyncio
import os
import sys
from app.config.settings import settings
from app.services.ingestion_service import IngestionService
from app.utils.logger import logger


async def main() -> None:
    """Execute document ingestion pipeline."""
    target_path = sys.argv[1] if len(sys.argv) > 1 else settings.handbook_path

    if not os.path.exists(target_path):
        logger.error(
            f"Handbook file not found at: '{target_path}'.\n"
            f"Please place your PDF at '{target_path}' or pass the path as an argument:\n"
            f"  just ingest <path_to_pdf>"
        )
        sys.exit(1)

    logger.info(f"Starting handbook ingestion from: {target_path}")
    service = IngestionService()
    result = await service.ingest_file(target_path)

    print("\n" + "=" * 60)
    print("           HANDBOOK INGESTION SUMMARY")
    print("=" * 60)
    print(f"  Filename:     {result['filename']}")
    print(f"  Document ID:  {result['document_id']}")
    print(f"  Total Pages:  {result['total_pages']}")
    print(f"  Total Chunks: {result['total_chunks']}")
    print(f"  Status:       {result['status']}")
    print(f"  Storage:      Qdrant ('student_handbook') + PostgreSQL ('documents')")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
