"""Audit trail controller for compliance and evaluation reporting.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Handles audit log retrieval and compliance metrics queries.
"""

from typing import Optional
from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.schemas.audit_schema import AuditLogItem, AuditSummaryResponse
from app.utils.response import success_response


class AuditController:
    """Controller providing audit trail querying for administrative evaluation."""

    @staticmethod
    async def get_logs(
        session: AsyncSession,
        limit: int = 50,
        decision: Optional[str] = None,
    ):
        """Retrieve recent security audit entries."""
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        if decision:
            stmt = stmt.where(AuditLog.decision == decision.upper())

        res = await session.execute(stmt)
        logs = res.scalars().all()

        items = [
            AuditLogItem(
                id=str(log.id),
                student_id=log.student_id,
                action=log.action,
                target_id=log.target_id,
                decision=log.decision,
                result=log.result,
                created_at=log.created_at,
            ).model_dump()
            for log in logs
        ]

        return success_response(
            status_code=status.HTTP_200_OK,
            message=f"Retrieved {len(items)} audit logs.",
            data=items,
        )

    @staticmethod
    async def get_summary(session: AsyncSession):
        """Aggregates audit compliance metrics for Assignment 2 reporting."""
        # Total count
        total_stmt = select(func.count(AuditLog.id))
        total_res = await session.execute(total_stmt)
        total_events = total_res.scalar() or 0

        # Counts by decision
        async def count_by_decision(dec: str) -> int:
            st = select(func.count(AuditLog.id)).where(AuditLog.decision == dec)
            r = await session.execute(st)
            return r.scalar() or 0

        allowed = await count_by_decision("ALLOWED")
        blocked = await count_by_decision("BLOCKED")
        approved = await count_by_decision("APPROVED")
        rejected = await count_by_decision("REJECTED")

        # Fetch 10 most recent logs
        recent_stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10)
        recent_res = await session.execute(recent_stmt)
        recent_logs = [
            AuditLogItem(
                id=str(log.id),
                student_id=log.student_id,
                action=log.action,
                target_id=log.target_id,
                decision=log.decision,
                result=log.result,
                created_at=log.created_at,
            )
            for log in recent_res.scalars().all()
        ]

        summary = AuditSummaryResponse(
            total_events=total_events,
            allowed_count=allowed,
            blocked_count=blocked,
            approved_count=approved,
            rejected_count=rejected,
            recent_logs=recent_logs,
        )

        return success_response(
            status_code=status.HTTP_200_OK,
            message="Audit summary generated successfully.",
            data=summary.model_dump(),
        )
