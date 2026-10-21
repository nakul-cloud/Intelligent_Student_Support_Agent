"""Student records inquiry service layer.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively fetches student academic, fee,
  scholarship, and ticket records from PostgreSQL.
- Dependency Inversion (DIP): Injects AsyncSession for testability.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.custom_exceptions import ResourceNotFoundError
from app.models.student_records import FeeRecord, Scholarship, Student, SupportTicket
from app.schemas.student_schema import (
    FeeSummaryResponse,
    ScholarshipResponse,
    StudentProfileResponse,
    SupportTicketResponse,
)


class StudentService:
    """Service providing read access to enrolled student enterprise records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_profile(self, student_id: str) -> StudentProfileResponse:
        """Retrieves student enrollment and programme profile."""
        stmt = select(Student).where(Student.student_id == student_id)
        res = await self.session.execute(stmt)
        student = res.scalar_one_or_none()
        if not student:
            raise ResourceNotFoundError(f"Student profile '{student_id}' not found.")

        return StudentProfileResponse(
            student_id=student.student_id,
            name=student.name,
            programme=student.programme,
            batch=student.batch,
            status=student.status,
        )

    async def get_fees(self, student_id: str) -> FeeSummaryResponse:
        """Retrieves tuition fee ledger for the student."""
        stmt = select(FeeRecord).where(FeeRecord.student_id == student_id)
        res = await self.session.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            raise ResourceNotFoundError(f"No fee ledger registered for student '{student_id}'.")

        return FeeSummaryResponse(
            student_id=record.student_id,
            total_fee=float(record.total_fee),
            paid=float(record.paid),
            pending=float(record.pending),
            due_date=record.due_date,
            status=record.status,
            receipt=record.receipt,
        )

    async def get_scholarship(self, student_id: str) -> Optional[ScholarshipResponse]:
        """Retrieves active scholarship award or returns None if not awarded."""
        stmt = select(Scholarship).where(Scholarship.student_id == student_id)
        res = await self.session.execute(stmt)
        schol = res.scalar_one_or_none()
        if not schol:
            return None

        return ScholarshipResponse(
            student_id=schol.student_id,
            scholarship_type=schol.scholarship_type,
            percentage=float(schol.percentage),
            amount_per_semester=float(schol.amount_per_semester),
            status=schol.status,
        )

    async def get_tickets(self, student_id: str) -> List[SupportTicketResponse]:
        """Retrieves all support grievance tickets logged by the student."""
        stmt = (
            select(SupportTicket)
            .where(SupportTicket.student_id == student_id)
            .order_by(SupportTicket.created_at.desc())
        )
        res = await self.session.execute(stmt)
        tickets = res.scalars().all()

        return [
            SupportTicketResponse(
                ticket_id=t.ticket_id,
                student_id=t.student_id,
                category=t.category,
                description=t.description,
                priority=t.priority,
                status=t.status,
                created_at=t.created_at,
            )
            for t in tickets
        ]
