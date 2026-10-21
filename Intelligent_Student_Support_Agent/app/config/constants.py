"""Single source of truth for all domain enums, status codes, and constants.

Follows enterprise clean architecture standards.
Prevents magic strings across routes, agents, tools, and services.
"""

from enum import StrEnum


class DocumentStatus(StrEnum):
    """Lifecycle states for ingested PDF files."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    EMBEDDED = "embedded"
    INSERTED = "inserted"
    FAILED = "failed"


class ConversationStatus(StrEnum):
    """States for student chat sessions."""

    ACTIVE = "active"
    CLOSED = "closed"


class MessageRole(StrEnum):
    """Message participant roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class FeeStatus(StrEnum):
    """Student tuition payment states."""

    PAID = "Paid"
    PARTIALLY_PAID = "Partially Paid"
    PENDING = "Pending"
    OVERDUE = "Overdue"


class ScholarshipStatus(StrEnum):
    """Scholarship award states."""

    ACTIVE = "Active"
    PENDING = "Pending"
    EXPIRED = "Expired"
    REVOKED = "Revoked"


class TicketPriority(StrEnum):
    """Priority levels for support tickets."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(StrEnum):
    """Lifecycle states for support tickets."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TerminationReason(StrEnum):
    """Agent loop termination reasons for local Tracer."""

    FINAL_ANSWER = "final_answer"
    MAX_TURNS = "max_turns"
    SECURITY_REJECTION = "security_rejection"
    TOOL_ERROR = "tool_error"


# Sensitive terms that must NEVER be persisted in student long-term memory
SENSITIVE_MEMORY_KEYWORDS: frozenset[str] = frozenset([
    "password",
    "otp",
    "pin",
    "cvv",
    "credit_card",
    "card_number",
    "secret",
    "ssn",
    "token",
])
