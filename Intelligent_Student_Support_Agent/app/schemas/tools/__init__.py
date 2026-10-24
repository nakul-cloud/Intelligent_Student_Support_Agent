"""Tool schemas package.

Exports individual tool schemas for LLM function calling:
- fee_schema.py: FEE_TOOL_SCHEMA
- scholarship_schema.py: SCHOLARSHIP_TOOL_SCHEMA
- ticket_schema.py: TICKET_TOOL_SCHEMA
- rag_schema.py: RAG_TOOL_SCHEMA
"""

from app.schemas.tools.auth_schema import UPDATE_STUDENT_PASSWORD_SCHEMA
from app.schemas.tools.fee_schema import FEE_TOOL_SCHEMA
from app.schemas.tools.profile_schema import UPDATE_STUDENT_PROFILE_SCHEMA
from app.schemas.tools.rag_schema import RAG_TOOL_SCHEMA
from app.schemas.tools.scholarship_schema import SCHOLARSHIP_TOOL_SCHEMA
from app.schemas.tools.ticket_schema import (
    GET_TICKET_STATUS_SCHEMA,
    LIST_STUDENT_TICKETS_SCHEMA,
    TICKET_TOOL_SCHEMA,
)

__all__ = [
    "FEE_TOOL_SCHEMA",
    "SCHOLARSHIP_TOOL_SCHEMA",
    "TICKET_TOOL_SCHEMA",
    "GET_TICKET_STATUS_SCHEMA",
    "LIST_STUDENT_TICKETS_SCHEMA",
    "RAG_TOOL_SCHEMA",
    "UPDATE_STUDENT_PASSWORD_SCHEMA",
    "UPDATE_STUDENT_PROFILE_SCHEMA",
]


