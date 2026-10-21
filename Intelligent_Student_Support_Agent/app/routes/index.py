"""Aggregates all domain API routers under a unified api_router ."""

from fastapi import APIRouter
from app.routes.ingestion_routes import router as ingestion_router
from app.routes.auth_routes import router as auth_router
from app.routes.student_routes import router as student_router
from app.routes.audit_routes import router as audit_router
from app.routes.chat_routes import router as chat_router

api_router = APIRouter()

# Register sub-routers
api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(student_router)
api_router.include_router(audit_router)
api_router.include_router(ingestion_router)

__all__ = ["api_router"]
