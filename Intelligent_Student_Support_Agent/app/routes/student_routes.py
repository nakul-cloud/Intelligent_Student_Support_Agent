"""FastAPI route endpoints for direct student records access.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Routes HTTP endpoints under /api/v1/student to StudentController.
- Security-by-Design: All endpoints enforce Bearer JWT verification via get_current_student dependency.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.controllers.student_controller import StudentController
from app.middlewares.auth import get_current_student

router = APIRouter(prefix="/student", tags=["Student Records"])


@router.get(
    "/profile",
    summary="Get authenticated student profile",
    status_code=status.HTTP_200_OK,
)
async def get_profile(
    student_id: str = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    """Retrieve profile and programme details for the authenticated student."""
    return await StudentController.get_profile(student_id=student_id, session=session)


@router.get(
    "/fees",
    summary="Get authenticated student fee ledger",
    status_code=status.HTTP_200_OK,
)
async def get_fees(
    student_id: str = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    """Retrieve fee ledger, installment status, and receipts for the authenticated student."""
    return await StudentController.get_fees(student_id=student_id, session=session)


@router.get(
    "/scholarship",
    summary="Get authenticated student scholarship record",
    status_code=status.HTTP_200_OK,
)
async def get_scholarship(
    student_id: str = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    """Retrieve scholarship award details if granted to the authenticated student."""
    return await StudentController.get_scholarship(student_id=student_id, session=session)


@router.get(
    "/tickets",
    summary="Get authenticated student support tickets",
    status_code=status.HTTP_200_OK,
)
async def get_tickets(
    student_id: str = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    """Retrieve all grievance and escalation tickets logged by the authenticated student."""
    return await StudentController.get_tickets(student_id=student_id, session=session)
