"""Chat controller handling agent turn submissions and session queries.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Validates chat requests, invokes ChatService,
  and maps domain outputs to standardized HTTP responses.
- Dependency Inversion (DIP): Injects AsyncSession into ChatService.
"""

from uuid import UUID
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat_schema import ChatRequest
from app.services.chat_service import ChatService
from app.utils.response import success_response


class ChatController:
    """Controller handling conversational agent turns and session lookups."""

    @staticmethod
    async def send_message(
        student_id: str,
        request: ChatRequest,
        session: AsyncSession,
    ):
        """Processes a chat turn with the AI support agent."""
        service = ChatService(session)
        chat_response = await service.process_turn(
            student_id=student_id,
            user_message=request.message,
            conversation_id=request.conversation_id,
        )
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Agent response generated successfully.",
            data=chat_response.model_dump(),
        )

    @staticmethod
    async def list_conversations(
        student_id: str,
        session: AsyncSession,
    ):
        """Retrieves list of active and past chat sessions for the student."""
        service = ChatService(session)
        conversations = await service.list_conversations(student_id)
        return success_response(
            status_code=status.HTTP_200_OK,
            message=f"Retrieved {len(conversations)} conversations.",
            data=[c.model_dump() for c in conversations],
        )

    @staticmethod
    async def get_messages(
        student_id: str,
        conversation_id: UUID,
        session: AsyncSession,
    ):
        """Retrieves full message turn history for a specific conversation."""
        service = ChatService(session)
        messages = await service.get_conversation_messages(student_id, conversation_id)
        return success_response(
            status_code=status.HTTP_200_OK,
            message=f"Retrieved {len(messages)} messages.",
            data=[m.model_dump() for m in messages],
        )
