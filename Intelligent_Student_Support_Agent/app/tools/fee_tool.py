"""Student tuition fee and ledger inquiry tool.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for querying student tuition dues,
  payment receipts, and installment records from the PostgreSQL database.
- Authorization & Audit (Assignment 2): Enforces data ownership checks in tool code,
  blocking cross-student queries and generating audit records.
"""

from typing import Optional
from sqlalchemy import select
from app.config.database import AsyncSessionLocal
from app.exceptions.custom_exceptions import PermissionDeniedError
from app.models.student_records import FeeRecord, Student
from app.services.audit_service import log_audit_event
from app.utils.logger import logger
from app.utils.ownership import check_ownership


async def get_fee_status(
    student_id: str,
    requesting_student_id: Optional[str] = None,
) -> str:
    """Retrieve the current fee payment record and dues for a student.

    Queries the PostgreSQL database for the student's enrollment record
    and their tuition fee installment ledger.

    Args:
        student_id: The unique student identification code (e.g. 'STU001').
        requesting_student_id: Optional authenticated caller student ID for authorization check.

    Returns:
        A human-readable formatted string containing the student's fee details,
        or an informative message if the record is missing or access is unauthorized.
    """
    clean_id = student_id.strip().upper()
    caller_id = (requesting_student_id or clean_id).strip().upper()
    logger.info(f"FeeTool: Caller '{caller_id}' querying fee status for target '{clean_id}'...")

    # 1. Enforce Code-Level Authorization / Ownership Check
    if requesting_student_id:
        try:
            check_ownership(
                requesting_student_id=requesting_student_id,
                target_student_id=clean_id,
            )
        except PermissionDeniedError as perm_err:
            await log_audit_event(
                student_id=caller_id,
                action="fee_tool",
                target_id=clean_id,
                decision="BLOCKED",
                result="Cross-student private record access denied",
            )
            return (
                f"ACCESS DENIED: You are not authorized to view the private fee records "
                f"of student '{clean_id}'. You may only access your own records."
            )

    try:
        async with AsyncSessionLocal() as session:
            # 2. Verify student exists in the university directory
            student_stmt = select(Student).where(Student.student_id == clean_id)
            student_result = await session.execute(student_stmt)
            student = student_result.scalar_one_or_none()

            if not student:
                logger.warning(f"FeeTool: Student '{clean_id}' not found in database.")
                await log_audit_event(
                    student_id=caller_id,
                    action="fee_tool",
                    target_id=clean_id,
                    decision="ALLOWED",
                    result=f"Student '{clean_id}' not found in directory",
                )
                return f"No student found with ID '{clean_id}'. Please verify the student ID."

            # 3. Query the student's fee ledger record
            fee_stmt = select(FeeRecord).where(FeeRecord.student_id == clean_id)
            fee_result = await session.execute(fee_stmt)
            fee_record = fee_result.scalar_one_or_none()

            if not fee_record:
                logger.info(f"FeeTool: No fee record on file for student '{clean_id}'.")
                await log_audit_event(
                    student_id=caller_id,
                    action="fee_tool",
                    target_id=clean_id,
                    decision="ALLOWED",
                    result="No fee record on file",
                )
                return (
                    f"Student: {student.name} ({student.student_id})\n"
                    f"Programme: {student.programme} (Batch: {student.batch})\n"
                    f"Fee Status: No fee records are currently registered for this student."
                )

            # 4. Format the fee details
            receipt_info = (
                f"Receipt #{fee_record.receipt}"
                if fee_record.receipt
                else "None (Pending Payment)"
            )
            result_str = (
                f"Student Name: {student.name} (ID: {student.student_id})\n"
                f"Programme: {student.programme} | Batch: {student.batch}\n"
                f"Enrollment Status: {student.status}\n"
                f"Total Tuition Fee: INR {fee_record.total_fee:,.2f}\n"
                f"Amount Paid: INR {fee_record.paid:,.2f}\n"
                f"Pending Dues: INR {fee_record.pending:,.2f}\n"
                f"Due Date: {fee_record.due_date}\n"
                f"Payment Status: {fee_record.status}\n"
                f"Last Payment Receipt: {receipt_info}"
            )

            # 5. Log audit trail for permitted access
            await log_audit_event(
                student_id=caller_id,
                action="fee_tool",
                target_id=clean_id,
                decision="ALLOWED",
                result=f"Fee status retrieved (Status: {fee_record.status})",
            )

            logger.info(f"FeeTool: Fee status retrieved for '{clean_id}' (Status: {fee_record.status}).")
            return result_str

    except Exception as exc:
        logger.error(f"FeeTool: Error querying fee status for '{clean_id}': {exc}")
        return f"Database error while querying fee records for student '{clean_id}': {str(exc)}"
