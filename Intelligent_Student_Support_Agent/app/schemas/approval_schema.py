"""Pydantic schemas for sensitive action human-in-the-loop approval.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively defines validation contracts for
  human confirmation and sensitive action states.
"""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    """Status lifecycle for sensitive actions requiring confirmation."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalRequest(BaseModel):
    """Payload representing a pending sensitive action requiring confirmation."""

    action: str = Field(..., description="Sensitive action name (e.g., update_contact)")
    student_id: str = Field(..., description="Student requesting the action")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Action parameters and context"
    )
    status: ApprovalStatus = Field(
        default=ApprovalStatus.PENDING, description="Current approval status"
    )


class ApprovalDecision(BaseModel):
    """Payload representing a confirmation response from the user."""

    confirmed: bool = Field(
        ...,
        description="True if student explicitly confirms (e.g. YES), False if rejected (e.g. NO)",
    )
    reason: Optional[str] = Field(None, description="Optional cancellation or approval note")
