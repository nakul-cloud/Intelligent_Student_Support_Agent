"""Student scholarship awards and financial aid inquiry tool.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for checking student scholarship grants,
  fellowships, and tuition waiver records from the PostgreSQL database.
- Separation of Concerns: Contains only Python execution logic; schemas are decoupled
  in the app/schemas/ layer.
"""

from sqlalchemy import select
from app.config.database import AsyncSessionLocal
from app.models.student_records import Scholarship, Student
from app.utils.logger import logger


async def check_scholarship(student_id: str) -> str:
    """Check active scholarship grants and financial aid awards for a student.

    Queries the PostgreSQL database to determine if the student has been granted
    a merit, sports, or research fellowship scholarship.

    Args:
        student_id: The unique student identification code (e.g. 'STU001').

    Returns:
        A human-readable formatted string with scholarship grant details,
        or an informative notice if no scholarship exists.
    """
    clean_id = student_id.strip().upper()
    logger.info(f"ScholarshipTool: Checking scholarship records for student ID '{clean_id}'...")

    try:
        async with AsyncSessionLocal() as session:
            # 1. Verify student existence
            student_stmt = select(Student).where(Student.student_id == clean_id)
            student_result = await session.execute(student_stmt)
            student = student_result.scalar_one_or_none()

            if not student:
                return f"No student found with ID '{clean_id}'. Please verify the student ID."

            # 2. Query scholarship award records
            schol_stmt = select(Scholarship).where(Scholarship.student_id == clean_id)
            schol_result = await session.execute(schol_stmt)
            scholarship = schol_result.scalar_one_or_none()

            if not scholarship:
                logger.info(f"ScholarshipTool: No active scholarship for student '{clean_id}'.")
                return (
                    f"Student: {student.name} (ID: {student.student_id})\n"
                    f"Programme: {student.programme} (Batch: {student.batch})\n"
                    f"Scholarship Award: No active scholarship or financial grant found on record."
                )

            # 3. Format scholarship details
            result_str = (
                f"Student Name: {student.name} (ID: {student.student_id})\n"
                f"Programme: {student.programme} | Batch: {student.batch}\n"
                f"Scholarship Scheme: {scholarship.scholarship_type}\n"
                f"Fee Waiver Percentage: {scholarship.percentage}%\n"
                f"Grant Amount Per Semester: INR {scholarship.amount_per_semester:,.2f}\n"
                f"Award Status: {scholarship.status}"
            )

            logger.info(f"ScholarshipTool: Details retrieved for '{clean_id}' ({scholarship.scholarship_type}).")
            return result_str

    except Exception as exc:
        logger.error(f"ScholarshipTool: Error checking scholarship for '{clean_id}': {exc}")
        return f"Database error while querying scholarship records for student '{clean_id}': {str(exc)}"
