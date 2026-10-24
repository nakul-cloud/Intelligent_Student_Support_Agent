"""Central registry and aggregator for agent tool schemas and dispatch mappings.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively acts as the registry aggregating modular tool schemas and callables.
- Open/Closed (OCP): New tools are plugged in by importing their schema and function into the registry.
- Dependency Inversion (DIP): Aggregates modular tool contracts without implementing domain business logic.
"""

from typing import Any, Callable, Coroutine
from app.schemas.tools import (
    FEE_TOOL_SCHEMA,
    GET_TICKET_STATUS_SCHEMA,
    LIST_STUDENT_TICKETS_SCHEMA,
    RAG_TOOL_SCHEMA,
    SCHOLARSHIP_TOOL_SCHEMA,
    TICKET_TOOL_SCHEMA,
    UPDATE_STUDENT_PASSWORD_SCHEMA,
    UPDATE_STUDENT_PROFILE_SCHEMA,
)
from app.tools import (
    check_scholarship,
    create_support_ticket,
    get_fee_status,
    get_ticket_status,
    list_student_tickets,
    search_student_handbook,
    update_student_password,
    update_student_profile,
)

# ==============================================================================
# Master Tool Schemas List for LLM Function Calling (Groq / Provider-Agnostic)
# ==============================================================================

TOOL_SCHEMAS: list[dict[str, Any]] = [
    RAG_TOOL_SCHEMA,
    FEE_TOOL_SCHEMA,
    SCHOLARSHIP_TOOL_SCHEMA,
    TICKET_TOOL_SCHEMA,
    GET_TICKET_STATUS_SCHEMA,
    LIST_STUDENT_TICKETS_SCHEMA,
    UPDATE_STUDENT_PASSWORD_SCHEMA,
    UPDATE_STUDENT_PROFILE_SCHEMA,
]

# ==============================================================================
# Master Dispatch Map: Function Name String -> Callable Async Coroutine
# ==============================================================================

TOOL_MAP: dict[str, Callable[..., Coroutine[Any, Any, str]]] = {
    "search_student_handbook": search_student_handbook,
    "get_fee_status": get_fee_status,
    "check_scholarship": check_scholarship,
    "create_support_ticket": create_support_ticket,
    "get_ticket_status": get_ticket_status,
    "list_student_tickets": list_student_tickets,
    "update_student_password": update_student_password,
    "update_student_profile": update_student_profile,
}


