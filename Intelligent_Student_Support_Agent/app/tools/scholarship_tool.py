"""Student scholarship awards and financial aid inquiry tool.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for checking student scholarship grants,
  fellowships, and tuition waiver records from the PostgreSQL database.
- Authorization & Audit (Assignment 2): Enforces data ownership checks in tool code,
  blocking cross-student queries and generating audit records.
"""

from typing import Optional
from sqlalchemy import select
from app.config.database import AsyncSessionLocal
from app.exceptions.custom_exceptions import PermissionDeniedError
from app.models.student_records import Scholarship, Student
from app.services.audit_service import log_audit_event
from app.utils.logger import logger
from app.utils.ownership import check_ownership


async def check_scholarship(
    student_id: Optional[str] = None,
    requesting_student_id: Optional[str] = None,
) -> str:
    """Check active scholarship grants and financial aid awards for a student.

    Queries the PostgreSQL database to determine if the student has been granted
    a merit, sports, or research fellowship scholarship.

    Args:
        student_id: The unique student identification code (e.g. 'STU001').
        requesting_student_id: Optional authenticated caller student ID for authorization check.

    Returns:
        A human-readable formatted string with scholarship grant details,
        or an informative notice if no scholarship exists or access is denied.
    """
    target_id = student_id or requesting_student_id
    if not target_id:
        return "Error: No student ID provided to check scholarship records."
    clean_id = target_id.strip().upper()
    caller_id = (requesting_student_id or clean_id).strip().upper()
    logger.info(f"ScholarshipTool: Caller '{caller_id}' querying scholarship for '{clean_id}'...")

    # 1. Enforce Code-Level Authorization / Ownership Check
    if requesting_student_id:
        try:
            check_ownership(
                requesting_student_id=requesting_student_id,
                target_student_id=clean_id,
            )
        except PermissionDeniedError:
            await log_audit_event(
                student_id=caller_id,
                action="scholarship_tool",
                target_id=clean_id,
                decision="BLOCKED",
                result="Cross-student private record access denied",
            )
            return (
                f"ACCESS DENIED: You are not authorized to view the private scholarship "
                f"records of student '{clean_id}'. You may only access your own records."
            )

    try:
        async with AsyncSessionLocal() as session:
            # 2. Verify student existence
            student_stmt = select(Student).where(Student.student_id == clean_id)
            student_result = await session.execute(student_stmt)
            student = student_result.scalar_one_or_none()

            if not student:
                await log_audit_event(
                    student_id=caller_id,
                    action="scholarship_tool",
                    target_id=clean_id,
                    decision="ALLOWED",
                    result=f"Student '{clean_id}' not found",
                )
                return f"No student found with ID '{clean_id}'. Please verify the student ID."

            # 3. Query scholarship award records
            schol_stmt = select(Scholarship).where(Scholarship.student_id == clean_id)
            schol_result = await session.execute(schol_stmt)
            scholarship = schol_result.scalar_one_or_none()

            if not scholarship:
                logger.info(f"ScholarshipTool: No active scholarship for student '{clean_id}'.")
                await log_audit_event(
                    student_id=caller_id,
                    action="scholarship_tool",
                    target_id=clean_id,
                    decision="ALLOWED",
                    result="No active scholarship on record",
                )
                return (
                    f"Student: {student.name} (ID: {student.student_id})\n"
                    f"Programme: {student.programme} (Batch: {student.batch})\n"
                    f"Scholarship Award: No active scholarship or financial grant found on record."
                )

            # 4. Format scholarship details
            result_str = (
                f"Student Name: {student.name} (ID: {student.student_id})\n"
                f"Programme: {student.programme} | Batch: {student.batch}\n"
                f"Scholarship Scheme: {scholarship.scholarship_type}\n"
                f"Fee Waiver Percentage: {scholarship.percentage}%\n"
                f"Grant Amount Per Semester: INR {scholarship.amount_per_semester:,.2f}\n"
                f"Award Status: {scholarship.status}"
            )

            # 5. Record permitted audit log
            await log_audit_event(
                student_id=caller_id,
                action="scholarship_tool",
                target_id=clean_id,
                decision="ALLOWED",
                result=f"Scholarship details retrieved ({scholarship.scholarship_type})",
            )

            logger.info(f"ScholarshipTool: Details retrieved for '{clean_id}' ({scholarship.scholarship_type}).")
            return result_str

    except Exception as exc:
        logger.error(f"ScholarshipTool: Error checking scholarship for '{clean_id}': {exc}")
        return f"Database error while querying scholarship records for student '{clean_id}': {str(exc)}"
