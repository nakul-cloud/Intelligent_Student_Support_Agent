"""FastAPI route endpoints for multi-turn student agent interactions.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Routes HTTP requests under /api/v1/chat to ChatController.
- Security-by-Design: All chat routes enforce Bearer JWT verification via get_current_student.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.controllers.chat_controller import ChatController
from app.middlewares.auth import get_current_student
from app.schemas.chat_schema import ChatRequest

router = APIRouter(prefix="/chat", tags=["Agent Chat"])


@router.post(
    "",
    summary="Submit user query to multi-turn student support agent",
    status_code=status.HTTP_200_OK,
)
async def chat(
    request: ChatRequest,
    student_id: str = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    """Executes a multi-turn ReAct agent loop turn with two-tier memory, tools, and tracing."""
    return await ChatController.send_message(
        student_id=student_id,
        request=request,
        session=session,
    )


@router.get(
    "/conversations",
    summary="List student conversation sessions",
    status_code=status.HTTP_200_OK,
)
async def list_conversations(
    student_id: str = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    """Lists past and current chat sessions initiated by the authenticated student."""
    return await ChatController.list_conversations(
        student_id=student_id,
        session=session,
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    summary="Get full conversation history",
    status_code=status.HTTP_200_OK,
)
async def get_conversation_messages(
    conversation_id: UUID,
    student_id: str = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    """Retrieves all historical message turns and trace IDs for a conversation."""
    return await ChatController.get_messages(
        student_id=student_id,
        conversation_id=conversation_id,
        session=session,
    )
