"""Pydantic schemas for security audit trail reporting and evaluation compliance.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively defines contracts for audit inspection endpoints.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AuditLogItem(BaseModel):
    """Single immutable audit log entry."""

    id: str
    student_id: str
    action: str
    target_id: Optional[str] = None
    decision: str  # ALLOWED, BLOCKED, APPROVED, REJECTED
    result: Optional[str] = None
    created_at: datetime


class AuditSummaryResponse(BaseModel):
    """Aggregated compliance metrics required for Assignment 2 evaluation."""

    total_events: int
    allowed_count: int
    blocked_count: int
    approved_count: int
    rejected_count: int
    recent_logs: List[AuditLogItem] = Field(default_factory=list)
