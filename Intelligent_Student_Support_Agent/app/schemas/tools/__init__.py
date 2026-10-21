"""Tool schemas package.

Exports individual tool schemas for LLM function calling:
- fee_schema.py: FEE_TOOL_SCHEMA
- scholarship_schema.py: SCHOLARSHIP_TOOL_SCHEMA
- ticket_schema.py: TICKET_TOOL_SCHEMA
- rag_schema.py: RAG_TOOL_SCHEMA
"""

from app.schemas.tools.fee_schema import FEE_TOOL_SCHEMA
from app.schemas.tools.rag_schema import RAG_TOOL_SCHEMA
from app.schemas.tools.scholarship_schema import SCHOLARSHIP_TOOL_SCHEMA
from app.schemas.tools.ticket_schema import TICKET_TOOL_SCHEMA

__all__ = [
    "FEE_TOOL_SCHEMA",
    "SCHOLARSHIP_TOOL_SCHEMA",
    "TICKET_TOOL_SCHEMA",
    "RAG_TOOL_SCHEMA",
]
