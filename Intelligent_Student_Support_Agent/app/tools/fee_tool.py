"""Student tuition fee and ledger inquiry tool.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for querying student tuition dues,
  payment receipts, and installment records from the PostgreSQL database.
- Separation of Concerns: Contains only Python execution logic; schemas are decoupled
  in the app/schemas/ layer.
"""

from sqlalchemy import select
from app.config.database import AsyncSessionLocal
from app.models.student_records import FeeRecord, Student
from app.utils.logger import logger


async def get_fee_status(student_id: str) -> str:
    """Retrieve the current fee payment record and dues for a student.

    Queries the PostgreSQL database for the student's enrollment record
    and their tuition fee installment ledger.

    Args:
        student_id: The unique student identification code (e.g. 'STU001').

    Returns:
        A human-readable formatted string containing the student's fee details,
        or an informative message if the record is missing.
    """
    clean_id = student_id.strip().upper()
    logger.info(f"FeeTool: Querying fee status for student ID '{clean_id}'...")

    try:
        async with AsyncSessionLocal() as session:
            # 1. Verify student exists in the university directory
            student_stmt = select(Student).where(Student.student_id == clean_id)
            student_result = await session.execute(student_stmt)
            student = student_result.scalar_one_or_none()

            if not student:
                logger.warning(f"FeeTool: Student '{clean_id}' not found in database.")
                return f"No student found with ID '{clean_id}'. Please verify the student ID."

            # 2. Query the student's fee ledger record
            fee_stmt = select(FeeRecord).where(FeeRecord.student_id == clean_id)
            fee_result = await session.execute(fee_stmt)
            fee_record = fee_result.scalar_one_or_none()

            if not fee_record:
                logger.info(f"FeeTool: No fee record on file for student '{clean_id}'.")
                return (
                    f"Student: {student.name} ({student.student_id})\n"
                    f"Programme: {student.programme} (Batch: {student.batch})\n"
                    f"Fee Status: No fee records are currently registered for this student."
                )

            # 3. Format the fee details in clear, structured text for the agent to synthesize
            receipt_info = f"Receipt #{fee_record.receipt}" if fee_record.receipt else "None (Pending Payment)"
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

            logger.info(f"FeeTool: Fee status retrieved for '{clean_id}' (Status: {fee_record.status}).")
            return result_str

    except Exception as exc:
        logger.error(f"FeeTool: Error querying fee status for '{clean_id}': {exc}")
        return f"Database error while querying fee records for student '{clean_id}': {str(exc)}"
