"""FastAPI route endpoints for audit inspection and compliance evaluation.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Routes HTTP endpoints under /api/v1/audit to AuditController.
- Evaluation Support: Provides measurable audit evidence required by Assignment 2 brief.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.controllers.audit_controller import AuditController

router = APIRouter(prefix="/audit", tags=["Audit & Compliance"])


@router.get(
    "/logs",
    summary="List security audit logs",
    status_code=status.HTTP_200_OK,
)
async def list_logs(
    limit: int = Query(50, ge=1, le=200, description="Max logs to return"),
    decision: Optional[str] = Query(None, description="Filter by ALLOWED, BLOCKED, APPROVED, REJECTED"),
    session: AsyncSession = Depends(get_db),
):
    """Query immutable audit records showing tool calls, caller student ID, decision, and result."""
    return await AuditController.get_logs(session=session, limit=limit, decision=decision)


@router.get(
    "/summary",
    summary="Get aggregated compliance metrics for Assignment 2 evaluation",
    status_code=status.HTTP_200_OK,
)
async def get_summary(
    session: AsyncSession = Depends(get_db),
):
    """Returns total events and breakdown of ALLOWED, BLOCKED, APPROVED, and REJECTED counts."""
    return await AuditController.get_summary(session=session)
