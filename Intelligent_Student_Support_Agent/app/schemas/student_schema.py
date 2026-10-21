"""Pydantic schemas for student profile, fee records, scholarships, and tickets.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively defines data contracts for student data endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StudentProfileResponse(BaseModel):
    """Enrolled student demographic and programme profile."""

    student_id: str
    name: str
    programme: str
    batch: str
    status: str


class FeeSummaryResponse(BaseModel):
    """Tuition fee ledger breakdown."""

    student_id: str
    total_fee: float
    paid: float
    pending: float
    due_date: str
    status: str
    receipt: Optional[str] = None


class ScholarshipResponse(BaseModel):
    """Financial grant and scholarship details."""

    student_id: str
    scholarship_type: str
    percentage: float
    amount_per_semester: float
    status: str


class SupportTicketResponse(BaseModel):
    """Support grievance or administrative escalation ticket."""

    ticket_id: str
    student_id: str
    category: str
    description: str
    priority: str
    status: str
    created_at: datetime
