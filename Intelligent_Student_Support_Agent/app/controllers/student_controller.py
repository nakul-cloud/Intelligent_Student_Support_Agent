"""Student records controller handling profile, fee, scholarship, and ticket endpoints.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Validates student HTTP requests and returns standardized responses.
- Dependency Inversion (DIP): Injects AsyncSession into StudentService.
"""

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.student_service import StudentService
from app.utils.response import success_response


class StudentController:
    """Controller orchestrating student profile, fee, and scholarship lookups."""

    @staticmethod
    async def get_profile(student_id: str, session: AsyncSession):
        """Fetch profile of authenticated student."""
        service = StudentService(session)
        profile = await service.get_profile(student_id)
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Student profile retrieved successfully.",
            data=profile.model_dump(),
        )

    @staticmethod
    async def update_profile(student_id: str, request, session: AsyncSession):
        """Update profile details of authenticated student."""
        service = StudentService(session)
        profile = await service.update_profile(
            student_id=student_id,
            phone=request.phone,
            email=request.email,
            address=request.address,
        )
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Student profile updated successfully.",
            data=profile.model_dump(),
        )


    @staticmethod
    async def get_fees(student_id: str, session: AsyncSession):
        """Fetch tuition fee ledger for authenticated student."""
        service = StudentService(session)
        fees = await service.get_fees(student_id)
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Fee ledger retrieved successfully.",
            data=fees.model_dump(),
        )

    @staticmethod
    async def get_scholarship(student_id: str, session: AsyncSession):
        """Fetch active scholarship record for authenticated student."""
        service = StudentService(session)
        schol = await service.get_scholarship(student_id)
        if not schol:
            return success_response(
                status_code=status.HTTP_200_OK,
                message="No active scholarship award on record.",
                data=None,
            )
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Scholarship details retrieved successfully.",
            data=schol.model_dump(),
        )

    @staticmethod
    async def get_tickets(student_id: str, session: AsyncSession):
        """Fetch support tickets created by authenticated student."""
        service = StudentService(session)
        tickets = await service.get_tickets(student_id)
        return success_response(
            status_code=status.HTTP_200_OK,
            message=f"Retrieved {len(tickets)} support tickets.",
            data=[t.model_dump() for t in tickets],
        )
