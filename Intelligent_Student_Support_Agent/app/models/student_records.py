"""SQLAlchemy models for simulated student enterprise records and support tickets."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.config.constants import FeeStatus, ScholarshipStatus, TicketPriority, TicketStatus
from app.models.base import BaseModel


class Student(BaseModel):
    """Student profile directory table."""

    __tablename__ = "students"

    student_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    programme: Mapped[str] = mapped_column(String, nullable=False)
    batch: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="Enrolled", nullable=False)


class FeeRecord(BaseModel):
    """Student tuition and fee ledger table."""

    __tablename__ = "fee_records"

    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("students.student_id", ondelete="CASCADE"), index=True, nullable=False
    )
    total_fee: Mapped[int] = mapped_column(Integer, nullable=False)
    paid: Mapped[int] = mapped_column(Integer, nullable=False)
    pending: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default=FeeStatus.PENDING.value, nullable=False)
    receipt: Mapped[str | None] = mapped_column(String, nullable=True)


class Scholarship(BaseModel):
    """Student scholarship award table."""

    __tablename__ = "scholarships"

    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("students.student_id", ondelete="CASCADE"), index=True, nullable=False
    )
    scholarship_type: Mapped[str] = mapped_column(String, nullable=False)
    percentage: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_per_semester: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, default=ScholarshipStatus.ACTIVE.value, nullable=False)


class SupportTicket(BaseModel):
    """Student administrative support escalation tickets created by agent."""

    __tablename__ = "support_tickets"

    ticket_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    student_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String, default=TicketPriority.MEDIUM.value, nullable=False)
    status: Mapped[str] = mapped_column(String, default=TicketStatus.OPEN.value, nullable=False)
