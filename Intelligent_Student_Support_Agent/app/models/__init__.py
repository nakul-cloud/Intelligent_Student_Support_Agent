"""SQLAlchemy models package initialization.

Exports all ORM entities so Base.metadata is fully aware of all tables on startup.
"""

from app.models.base import Base, BaseModel, TimestampMixin, UUIDMixin
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.message import Message
from app.models.student_memory import StudentMemory
from app.models.student_records import FeeRecord, Scholarship, Student, SupportTicket

__all__ = [
    "Base",
    "BaseModel",
    "UUIDMixin",
    "TimestampMixin",
    "Conversation",
    "Message",
    "StudentMemory",
    "Document",
    "Student",
    "FeeRecord",
    "Scholarship",
    "SupportTicket",
]
