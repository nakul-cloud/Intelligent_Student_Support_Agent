"""Chat orchestration service integrating agent loop, memory, authorization, and persistence.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Coordinates conversation sessions, turn messages,
  memory context injection, ReAct multi-turn agent execution, and memory updates.
- Dependency Inversion (DIP): Injects AsyncSession and Groq client.
- Security-by-Design: Wraps domain tools with authenticated student context.
"""

import time
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent_loop import run_agent
from app.agent.client import get_async_groq_client
from app.exceptions.custom_exceptions import PermissionDeniedError, ResourceNotFoundError
from app.memory.memory_manager import MemoryManager
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.student_records import Student
from app.prompts.system_prompt import build_system_prompt
from app.schemas.chat_schema import ChatResponse, ConversationSummary, MessageItem
from app.schemas.tool_schemas import TOOL_SCHEMAS
from app.services.approval_service import ApprovalService
from app.tools.auth_tool import update_student_password
from app.tools.fee_tool import get_fee_status
from app.tools.profile_tool import update_student_profile
from app.tools.rag_tool import search_student_handbook
from app.tools.scholarship_tool import check_scholarship
from app.tools.ticket_tool import (
    create_support_ticket,
    get_ticket_status,
    list_student_tickets,
)
from app.utils.logger import logger
from tracing.tracer import Tracer


class ChatService:
    """Service governing student conversational turn execution and session persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.memory_manager = MemoryManager(session)
        self.approval_service = ApprovalService()

    def _build_contextual_tool_map(self, student_id: str) -> Dict[str, Callable]:
        """Binds authenticated caller student_id to tools requiring ownership checks."""

        async def contextual_fee_status(**kwargs):
            if "student_id" not in kwargs or not kwargs["student_id"]:
                kwargs["student_id"] = student_id
            if "requesting_student_id" not in kwargs:
                kwargs["requesting_student_id"] = student_id
            return await get_fee_status(**kwargs)

        async def contextual_scholarship(**kwargs):
            if "student_id" not in kwargs or not kwargs["student_id"]:
                kwargs["student_id"] = student_id
            if "requesting_student_id" not in kwargs:
                kwargs["requesting_student_id"] = student_id
            return await check_scholarship(**kwargs)

        async def contextual_ticket(**kwargs):
            # Student always creates ticket for themselves
            if "student_id" not in kwargs or not kwargs["student_id"]:
                kwargs["student_id"] = student_id
            return await create_support_ticket(**kwargs)

        async def contextual_get_ticket_status(**kwargs):
            if "student_id" not in kwargs or not kwargs["student_id"]:
                kwargs["student_id"] = student_id
            return await get_ticket_status(**kwargs)

        async def contextual_list_student_tickets(**kwargs):
            if "student_id" not in kwargs or not kwargs["student_id"]:
                kwargs["student_id"] = student_id
            return await list_student_tickets(**kwargs)

        async def contextual_update_password(**kwargs):
            if "student_id" not in kwargs or not kwargs["student_id"]:
                kwargs["student_id"] = student_id
            return await update_student_password(**kwargs)

        async def contextual_update_profile(**kwargs):
            if "student_id" not in kwargs or not kwargs["student_id"]:
                kwargs["student_id"] = student_id
            return await update_student_profile(**kwargs)

        return {
            "get_fee_status": contextual_fee_status,
            "check_scholarship": contextual_scholarship,
            "create_support_ticket": contextual_ticket,
            "get_ticket_status": contextual_get_ticket_status,
            "list_student_tickets": contextual_list_student_tickets,
            "update_student_password": contextual_update_password,
            "update_student_profile": contextual_update_profile,
            "search_student_handbook": search_student_handbook,
        }



    async def get_or_create_conversation(
        self, student_id: str, conversation_id: Optional[UUID] = None, first_message: str = ""
    ) -> Conversation:
        """Retrieves an existing conversation owned by the student or creates a new session."""
        if conversation_id:
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            res = await self.session.execute(stmt)
            conversation = res.scalar_one_or_none()
            if not conversation:
                raise ResourceNotFoundError(f"Conversation '{conversation_id}' not found.")

            # Enforce that student cannot hijack another student's conversation
            if conversation.student_id != student_id:
                raise PermissionDeniedError("Access denied: You do not own this conversation.")

            return conversation

        # Create new conversation
        title_snippet = (first_message[:36] + "...") if len(first_message) > 36 else (first_message or "New Session")
        conversation = Conversation(
            student_id=student_id,
            title=title_snippet,
            status="active",
        )
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def list_conversations(self, student_id: str) -> List[ConversationSummary]:
        """Lists all conversation sessions owned by the authenticated student."""
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.student_id == student_id)
            .order_by(Conversation.created_at.desc())
        )
        res = await self.session.execute(stmt)
        conversations = res.scalars().all()

        summaries = []
        for conv in conversations:
            msg_count = len(conv.messages) if conv.messages else 0
            if msg_count > 0:
                summaries.append(
                    ConversationSummary(
                        id=str(conv.id),
                        student_id=conv.student_id,
                        title=conv.title,
                        status=conv.status,
                        created_at=conv.created_at,
                        message_count=msg_count,
                    )
                )
        return summaries

    async def delete_conversation(self, student_id: str, conversation_id: UUID) -> bool:
        """Deletes a conversation session and all its message turns."""
        conv = await self.get_or_create_conversation(student_id, conversation_id)
        from sqlalchemy import delete
        await self.session.execute(delete(Message).where(Message.conversation_id == conv.id))
        await self.session.delete(conv)
        await self.session.commit()
        logger.info(f"ChatService: Deleted conversation {conversation_id} for student {student_id}")
        return True


    async def get_conversation_messages(
        self, student_id: str, conversation_id: UUID
    ) -> List[MessageItem]:
        """Fetches full message history for an authenticated student's session."""
        conv = await self.get_or_create_conversation(student_id, conversation_id)
        stmt = (
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
        )
        res = await self.session.execute(stmt)
        msgs = res.scalars().all()

        return [
            MessageItem(
                id=str(m.id),
                role=m.role,
                content=m.content,
                meta_data=m.meta_data,
                created_at=m.created_at,
            )
            for m in msgs
        ]

    async def process_turn(
        self,
        student_id: str,
        user_message: str,
        conversation_id: Optional[UUID] = None,
        request_id: Optional[str] = None,
    ) -> ChatResponse:
        """Executes a single conversational agent turn with memory, tools, and full telemetry."""
        # 1. Obtain or initialize conversation
        conversation = await self.get_or_create_conversation(
            student_id=student_id,
            conversation_id=conversation_id,
            first_message=user_message,
        )

        # 2. Initialize Tracer with comprehensive correlation & student identity
        tracer = Tracer(agent_name="StudentSupportAgent")
        tracer.start(
            user_query=user_message,
            student_id=student_id,
            conversation_id=str(conversation.id),
            request_id=request_id,
        )

        # 3. Persist user turn
        user_turn = Message(
            conversation_id=conversation.id,
            role="user",
            content=user_message,
        )
        self.session.add(user_turn)
        await self.session.commit()

        # 4. Load Prior Conversation History (excluding current user turn)
        history_stmt = (
            select(Message)
            .where(Message.conversation_id == conversation.id, Message.id != user_turn.id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(20)
        )
        history_res = await self.session.execute(history_stmt)
        history_turns = list(reversed(history_res.scalars().all()))
        conversation_history = [
            {"role": turn.role, "content": turn.content}
            for turn in history_turns
        ]

        # 5. Fetch Student Profile for prompt identity injection
        res_stu = await self.session.execute(select(Student).where(Student.student_id == student_id))
        student_rec = res_stu.scalar_one_or_none()

        # 6. Load Two-Tier Student Memory (Redis L1 -> PostgreSQL L2)
        t_mem_load = time.perf_counter()
        memory_context = await self.memory_manager.load_memory(student_id)
        mem_load_ms = (time.perf_counter() - t_mem_load) * 1000.0

        mem_lines = [
            line.strip("- ").strip()
            for line in (memory_context or "").splitlines()
            if line.strip().startswith("-")
        ]
        loaded_keys = [line.split(":")[0].strip() for line in mem_lines if ":" in line]
        tracer.log_memory_event(
            action="load",
            student_id=student_id,
            count=len(mem_lines),
            keys=loaded_keys,
            latency_ms=mem_load_ms,
            details={"tier": "redis_or_postgres", "has_context": bool(memory_context)},
        )

        # 7. Build System Prompt with Authenticated Identity & Memory Context
        system_prompt = build_system_prompt(
            memory_context=memory_context,
            student_id=student_id,
            student_name=student_rec.name if student_rec else None,
            programme=student_rec.programme if student_rec else None,
            batch=student_rec.batch if student_rec else None,
        )

        # 8. Configure Contextual Domain Tool Map
        contextual_tools = self._build_contextual_tool_map(student_id)

        # 9. Run Multi-Turn Agent Loop with Conversation History
        assistant_reply = await run_agent(
            user_query=user_message,
            system_prompt=system_prompt,
            tool_schemas=TOOL_SCHEMAS,
            tool_map=contextual_tools,
            tracer=tracer,
            conversation_history=conversation_history,
        )
        trace_id = tracer.trace_id

        # 10. Persist Assistant Response
        assistant_turn = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_reply,
            meta_data={"trace_id": trace_id},
        )
        self.session.add(assistant_turn)
        await self.session.commit()

        # 11. Two-Tier Memory Update: Extract and Persist Safe Facts
        t_mem_save = time.perf_counter()
        combined_text = f"{user_message}\n{assistant_reply}"
        saved_facts = await self.memory_manager.save_memory(
            student_id=student_id, conversation_text=combined_text
        )
        mem_save_ms = (time.perf_counter() - t_mem_save) * 1000.0
        facts_learned_keys = [f.fact_key for f in saved_facts]
        tracer.log_memory_event(
            action="save",
            student_id=student_id,
            count=len(saved_facts),
            keys=facts_learned_keys,
            latency_ms=mem_save_ms,
            details={"facts": [{"key": f.fact_key, "val": f.fact_value} for f in saved_facts]},
        )

        # 12. Finalize Tracer metrics, render ASCII summary, and write JSON artifact
        trace_data = tracer.finish()

        return ChatResponse(
            conversation_id=str(conversation.id),
            message=assistant_reply,
            role="assistant",
            trace_id=trace_id,
            facts_learned=facts_learned_keys,
            pending_approval=False,
            trace=trace_data,
        )

    async def chat(
        self,
        student_id: str,
        message: str,
        conversation_id: Optional[UUID | str] = None,
        debug: bool = False,
        request_id: Optional[str] = None,
    ) -> ChatResponse:
        """Alias for process_turn providing intuitive parameter naming."""
        conv_uuid = None
        if conversation_id:
            if isinstance(conversation_id, str):
                conv_uuid = UUID(conversation_id)
            elif isinstance(conversation_id, UUID):
                conv_uuid = conversation_id

        return await self.process_turn(
            student_id=student_id,
            user_message=message,
            conversation_id=conv_uuid,
            request_id=request_id,
        )
