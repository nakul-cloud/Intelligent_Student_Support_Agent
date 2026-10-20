"""Controller for handling document ingestion HTTP requests."""

from fastapi import UploadFile, status
from app.exceptions.custom_exceptions import AppError
from app.services.ingestion_service import IngestionService
from app.utils.logger import logger
from app.utils.response import success_response


class IngestionController:
    """Controller orchestrating file upload validation and ingestion service calls."""

    @staticmethod
    async def ingest_document(file: UploadFile):
        """Validate uploaded PDF and trigger synchronous ingestion and indexing."""
        if not file.filename.lower().endswith(".pdf"):
            raise AppError("Only PDF files are supported for ingestion.", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            file_bytes = await file.read()
            if not file_bytes:
                raise AppError("Uploaded file is empty.", status_code=status.HTTP_400_BAD_REQUEST)

            service = IngestionService()
            result = await service.ingest_bytes(file_bytes=file_bytes, filename=file.filename)

            return success_response(
                status_code=status.HTTP_201_CREATED,
                message=f"Document '{file.filename}' successfully parsed, chunked, and embedded into Qdrant.",
                data=result,
            )
        except AppError:
            raise
        except Exception as exc:
            logger.error(f"IngestionController error: {exc}")
            raise AppError(f"Document ingestion failed: {exc}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exc
