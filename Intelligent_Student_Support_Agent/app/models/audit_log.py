"""SQLAlchemy model for permanent security audit trail records.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively models the audit_logs persistence layer.
- Conformance: Records who requested the action, what was attempted,
  the permission decision (ALLOWED, BLOCKED, APPROVED, REJECTED), and the outcome.
"""

from typing import Optional
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class AuditLog(BaseModel):
    """Immutable audit trail recording security actions, access checks, and approval decisions."""

    __tablename__ = "audit_logs"

    student_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String, nullable=False, index=True)
    target_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    decision: Mapped[str] = mapped_column(String, nullable=False, index=True)
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
