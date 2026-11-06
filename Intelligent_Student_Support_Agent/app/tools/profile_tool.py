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
    confirmed: bool = False,
) -> str:
    """Updates the student's contact details (phone, email, address) in the database.

    Enforces Human-in-the-Loop Approval Gate for sensitive mutations:
    - If confirmed is False:
        Does NOT modify the database. Logs an audit record with decision='PENDING'
        and returns a PENDING_APPROVAL response prompting the student for explicit confirmation.
    - If confirmed is True:
        Applies and commits the updates to the database, logs an audit record with
        decision='APPROVED', and returns a success confirmation.

    Args:
        student_id: The unique student identification code (e.g. 'STU001').
        phone: Optional new phone or mobile number (e.g. '+91 98765 43210').
        email: Optional new email address.
        address: Optional new residential or campus hostel address.
        confirmed: Whether the student has explicitly approved this sensitive mutation.

    Returns:
        A human-readable confirmation string detailing the pending or completed update.
    """
    clean_id = student_id.strip().upper()
    logger.info(
        f"ProfileTool: Processing contact profile update for student '{clean_id}' (confirmed={confirmed})..."
    )

    if not phone and not email and not address:
        return "No updates specified. Please provide at least one field to update (phone, email, or address)."

    updated_fields = []
    if phone and phone.strip():
        updated_fields.append(f"Phone: {phone.strip()}")
    if email and email.strip():
        updated_fields.append(f"Email: {email.strip()}")
    if address and address.strip():
        updated_fields.append(f"Address: {address.strip()}")

    # 1. HUMAN-IN-THE-LOOP APPROVAL GATE:
    # If unconfirmed, block immediate execution and require explicit approval
    if not confirmed:
        await log_audit_event(
            student_id=clean_id,
            action="profile_update",
            target_id=clean_id,
            decision="PENDING",
            result=f"Approval gate triggered: Pending confirmation to update {', '.join(updated_fields)}.",
        )
        logger.info(f"ProfileTool: Approval gate triggered (PENDING) for student '{clean_id}'.")
        return (
            f"PENDING_APPROVAL: Modifying official student records ({', '.join(updated_fields)}) is a sensitive operation "
            f"requiring explicit student confirmation. Changes have NOT been saved to the database. "
            f"Please ask the student to explicitly confirm: 'Are you sure you want to update your {', '.join(updated_fields)}? "
            f"Please reply YES to confirm or NO to cancel.'"
        )

    # 2. CONFIRMED MUTATION:
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Student).where(Student.student_id == clean_id)
            res = await session.execute(stmt)
            student = res.scalar_one_or_none()

            if not student:
                return f"Cannot update profile: No student found with ID '{clean_id}'."

            if phone and phone.strip():
                student.phone = phone.strip()
            if email and email.strip():
                student.email = email.strip()
            if address and address.strip():
                student.address = address.strip()

            await session.commit()
            await session.refresh(student)

            # Record audit log
            await log_audit_event(
                student_id=clean_id,
                action="profile_update",
                target_id=clean_id,
                decision="APPROVED",
                result=f"Student confirmed sensitive operation. Successfully updated: {', '.join(updated_fields)}",
            )

            logger.info(f"ProfileTool: Successfully updated profile for '{clean_id}' with confirmation.")
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
