"""FastAPI routes for document upload and policy ingestion."""

from typing import Annotated
from fastapi import APIRouter, File, UploadFile
from app.controllers.ingestion_controller import IngestionController

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("", summary="Upload and ingest a handbook PDF into Qdrant & PostgreSQL")
async def upload_handbook(
    file: Annotated[UploadFile, File(description="PDF handbook document to chunk and embed")],
):
    """Upload a student handbook or policy PDF.
    
    Extracts structural sections, generates chunks, computes embeddings,
    indexes into Qdrant, and creates a lifecycle audit record in PostgreSQL.
    """
    return await IngestionController.ingest_document(file=file)
