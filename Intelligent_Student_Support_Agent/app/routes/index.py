"""Aggregates all domain API routers under a unified api_router ."""

from fastapi import APIRouter
from app.routes.ingestion_routes import router as ingestion_router

api_router = APIRouter()

# Register sub-routers
api_router.include_router(ingestion_router)

__all__ = ["api_router"]
