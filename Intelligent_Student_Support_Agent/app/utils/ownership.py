"""Ownership authorization enforcement utility.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for verifying that the
  authenticated student owns the requested resource target.
- Defense in Depth: Enforces authorization directly in application and tool code,
  fulfilling the Assignment 2 mandate that authorization must not rely solely on LLM prompts.
"""

from app.exceptions.custom_exceptions import PermissionDeniedError
from app.utils.logger import logger


def check_ownership(
    requesting_student_id: str,
    target_student_id: str,
) -> None:
    """Verifies that the logged-in student matches the target student resource.

    Args:
        requesting_student_id: The authenticated student ID extracted from JWT.
        target_student_id: The student ID targeted by the query or action.

    Raises:
        PermissionDeniedError: If requesting student attempts to access another student's data.
    """
    if not requesting_student_id or not target_student_id:
        logger.warning("Ownership verification failed: missing student identifier.")
        raise PermissionDeniedError("Missing student identifier for authorization verification.")

    req = requesting_student_id.strip().upper()
    target = target_student_id.strip().upper()

    if req != target:
        msg = (
            f"Access Denied: Logged-in student '{requesting_student_id}' is not "
            f"authorized to access private records of student '{target_student_id}'."
        )
        logger.warning(f"SECURITY ALERT - Cross-student access blocked: {req} attempted to read {target}")
        raise PermissionDeniedError(msg)
