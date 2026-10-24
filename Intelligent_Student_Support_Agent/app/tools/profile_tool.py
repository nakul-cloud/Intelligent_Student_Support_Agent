"""Student profile contact information management tool.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively updates student contact details
  (phone, email, residential address) in the database with audit logging.
- Dependency Inversion (DIP): Injects AsyncSessionLocal for database operations.
"""

from typing import Optional
from sqlalchemy import select
from app.config.database import AsyncSessionLocal
from app.models.student_records import Student
from app.services.audit_service import log_audit_event
from app.utils.logger import logger


async def update_student_profile(
    student_id: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    address: Optional[str] = None,
) -> str:
    """Immediately updates the student's contact details (phone, email, address) in the database.

    Directly modifies the student directory record in the database so changes
    are immediately effective without requiring an administrative support ticket.

    Args:
        student_id: The unique student identification code (e.g. 'STU001').
        phone: Optional new phone or mobile number (e.g. '+91 98765 43210').
        email: Optional new email address.
        address: Optional new residential or campus hostel address.

    Returns:
        A human-readable confirmation string detailing the updated fields and current record.
    """
    clean_id = student_id.strip().upper()
    logger.info(f"ProfileTool: Updating contact profile for student '{clean_id}'...")

    if not phone and not email and not address:
        return "No updates specified. Please provide at least one field to update (phone, email, or address)."

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Student).where(Student.student_id == clean_id)
            res = await session.execute(stmt)
            student = res.scalar_one_or_none()

            if not student:
                return f"Cannot update profile: No student found with ID '{clean_id}'."

            updated_fields = []
            if phone and phone.strip():
                student.phone = phone.strip()
                updated_fields.append(f"Phone: {student.phone}")
            if email and email.strip():
                student.email = email.strip()
                updated_fields.append(f"Email: {student.email}")
            if address and address.strip():
                student.address = address.strip()
                updated_fields.append(f"Address: {student.address}")

            await session.commit()
            await session.refresh(student)

            # Record audit log
            await log_audit_event(
                student_id=clean_id,
                action="profile_update",
                target_id=clean_id,
                decision="ALLOWED",
                result=f"Updated student contact details: {', '.join(updated_fields)}",
            )

            logger.info(f"ProfileTool: Successfully updated profile for '{clean_id}'.")
            return (
                f"Student Profile Updated Successfully!\n"
                f"- Student ID: {student.student_id} ({student.name})\n"
                f"- Database Status: Synchronized & Saved\n"
                f"- Effective Time: Immediately\n\n"
                f"Updated Information:\n" + "\n".join([f"• {f}" for f in updated_fields]) + "\n\n"
                f"Your records have been updated immediately in the university database."
            )

    except Exception as exc:
        logger.error(f"ProfileTool: Error updating profile for '{clean_id}': {exc}")
        return f"Database error while updating profile for student '{clean_id}': {str(exc)}"
