"""Student authentication credential and password management tool.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively handles verified password updates
  in the database with bcrypt hashing and security audit logging.
- Dependency Inversion (DIP): Injects AsyncSessionLocal for database operations.
"""

from sqlalchemy import select
from app.config.database import AsyncSessionLocal
from app.models.auth_credentials import AuthCredentials
from app.models.student_records import Student
from app.services.audit_service import log_audit_event
from app.utils.security import hash_password
from app.utils.logger import logger



async def update_student_password(student_id: str, new_password: str) -> str:
    """Immediately updates the student's account password in the university database.

    Hashes the new password with bcrypt and directly commits the change to the
    auth_credentials database table so it takes effect instantly without administrative delay.

    Args:
        student_id: The unique student identification code (e.g. 'STU001').
        new_password: The new plaintext password to set (minimum 6 characters).

    Returns:
        A confirmation string verifying that the password has been updated in the database.
    """
    clean_id = student_id.strip().upper()
    password_str = (new_password or "").strip()

    if len(password_str) < 6:
        return "Password change rejected: The new password must be at least 6 characters long."

    logger.info(f"AuthTool: Updating password immediately for student '{clean_id}'...")

    try:
        async with AsyncSessionLocal() as session:
            # 1. Verify student exists in directory
            stu_stmt = select(Student).where(Student.student_id == clean_id)
            stu_res = await session.execute(stu_stmt)
            student = stu_res.scalar_one_or_none()
            if not student:
                return f"Cannot change password: No student found with ID '{clean_id}'."

            # 2. Hash new password
            hashed = hash_password(password_str)

            # 3. Upsert credentials record in database
            cred_stmt = select(AuthCredentials).where(AuthCredentials.student_id == clean_id)
            cred_res = await session.execute(cred_stmt)
            credentials = cred_res.scalar_one_or_none()

            if not credentials:
                credentials = AuthCredentials(student_id=clean_id, hashed_password=hashed)
                session.add(credentials)
            else:
                credentials.hashed_password = hashed

            await session.commit()
            logger.info(f"AuthTool: Password hash successfully committed to database for student '{clean_id}'.")

            # 4. Record audit log
            await log_audit_event(
                student_id=clean_id,
                action="password_change",
                target_id=clean_id,
                decision="ALLOWED",
                result="Student account password updated directly in database via agent.",
            )

            return (
                f"Password Updated Successfully!\n"
                f"- Student ID: {clean_id} ({student.name})\n"
                f"- Database Status: Synchronized & Committed\n"
                f"- Effective Time: Immediately\n\n"
                f"Your account password has been updated directly in the university records. "
                f"You can now use your new password to sign in immediately."
            )

    except Exception as exc:
        logger.error(f"AuthTool: Error updating password for '{clean_id}': {exc}")
        return f"Database error while updating password for student '{clean_id}': {str(exc)}"
