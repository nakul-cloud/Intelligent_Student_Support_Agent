"""SQLAlchemy model for persistent student facts and memory."""

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class StudentMemory(BaseModel):
    """Durable long-term memory storing classified facts across sessions."""

    __tablename__ = "student_memory"

    student_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    fact_key: Mapped[str] = mapped_column(String, nullable=False)
    fact_value: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "fact_key", name="uq_student_memory_fact"),
    )
