"""Tool definitions package.

Exports individual, modular domain tools adhering strictly to the Single Responsibility Principle:
- fee_tool.py: Tuition ledger inquiries
- scholarship_tool.py: Financial aid and grants
- ticket_tool.py: Administrative grievance ticketing
- rag_tool.py: University handbook policy retrieval
"""

from app.tools.fee_tool import get_fee_status
from app.tools.rag_tool import search_student_handbook
from app.tools.scholarship_tool import check_scholarship
from app.tools.ticket_tool import create_support_ticket

__all__ = [
    "get_fee_status",
    "check_scholarship",
    "create_support_ticket",
    "search_student_handbook",
]
