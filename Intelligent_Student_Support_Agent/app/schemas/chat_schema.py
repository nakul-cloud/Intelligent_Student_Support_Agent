"""Pydantic schemas for the agentic chat interface and session management.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively defines request and response models
  for conversational turn execution and session history.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Payload for submitting a prompt to the student support agent."""

    message: str = Field(
        ...,
        min_length=1,
        description="User message or query for the support agent",
        examples=["What are my tuition fee dues?"],
    )
    conversation_id: Optional[UUID] = Field(
        None,
        description="Optional ongoing conversation UUID. If omitted, a new session is initiated.",
    )


class ChatResponse(BaseModel):
    """Payload returned by the agent upon turn completion."""

    conversation_id: str = Field(..., description="Active session conversation UUID")
    message: str = Field(..., description="Assistant's synthesized response")
    role: str = Field("assistant", description="Message author role")
    trace_id: Optional[str] = Field(None, description="Local execution trace identifier")
    facts_learned: List[str] = Field(
        default_factory=list,
        description="Key facts extracted and persisted to long-term memory in this turn",
    )
    pending_approval: bool = Field(
        default=False,
        description="True if agent paused awaiting human confirmation on a sensitive action",
    )


class MessageItem(BaseModel):
    """Single turn message representation."""

    id: str = Field(..., description="Message UUID")
    role: str = Field(..., description="Author role (user or assistant)")
    content: str = Field(..., description="Message text content")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Associated turn metadata")
    created_at: datetime = Field(..., description="Timestamp of turn creation")


class ConversationSummary(BaseModel):
    """Summary representation of a student conversation session."""

    id: str = Field(..., description="Conversation UUID")
    student_id: str = Field(..., description="Owning student ID")
    title: Optional[str] = Field(None, description="Auto-generated or user-assigned session title")
    status: str = Field(..., description="Session state (active, archived)")
    created_at: datetime = Field(..., description="Session start timestamp")
    message_count: int = Field(0, description="Total turns in this session")
