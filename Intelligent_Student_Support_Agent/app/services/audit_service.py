"""Security and audit trail service for logging important student agent actions.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively manages recording audit trail entries
  in the audit_logs PostgreSQL table.
- Compliance: Conforms with Assignment 2 requirements to record who requested
  an action, what was attempted, authorization/approval decisions, and final results.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.utils.logger import logger


class AuditService:
    """Service managing persistence of immutable audit logs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log_action(
        self,
        student_id: str,
        action: str,
        target_id: Optional[str],
        decision: str,
        result: Optional[str] = None,
    ) -> AuditLog:
        """Records an action event into the audit trail.

        Args:
            student_id: Identifier of student who initiated the request.
            action: Action or tool name (e.g. 'fee_tool', 'scholarship_tool', 'ticket_tool').
            target_id: Target student ID or entity being accessed.
            decision: 'ALLOWED', 'BLOCKED', 'APPROVED', or 'REJECTED'.
            result: Outcome summary or error message.
        """
        audit_entry = AuditLog(
            student_id=student_id,
            action=action,
            target_id=target_id,
            decision=decision.upper(),
            result=result,
        )
        self.session.add(audit_entry)
        await self.session.commit()
        logger.info(
            f"AUDIT LOG recorded: [{decision.upper()}] student={student_id} "
            f"action={action} target={target_id} result={result}"
        )
        return audit_entry


async def log_audit_event(
    student_id: str,
    action: str,
    target_id: Optional[str],
    decision: str,
    result: Optional[str] = None,
    session: Optional[AsyncSession] = None,
) -> AuditLog:
    """Convenience helper to record an audit entry with or without an active session."""
    if session:
        service = AuditService(session)
        return await service.log_action(student_id, action, target_id, decision, result)

    async with AsyncSessionLocal() as new_session:
        service = AuditService(new_session)
        return await service.log_action(student_id, action, target_id, decision, result)
