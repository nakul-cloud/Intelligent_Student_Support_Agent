"""Function schema for the student tuition fee and dues tool.

Defines the JSON schema used by the Groq LLM to decide when and how
to invoke the get_fee_status tool.
"""

from typing import Any

FEE_TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_fee_status",
        "description": (
            "Retrieve a student's tuition fee installment ledger, paid amount, "
            "pending balance, payment due date, and payment status (Paid, Partially Paid, Overdue). "
            "Use this tool whenever a student inquires about their tuition dues, receipts, or fee deadlines."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "The unique student ID (e.g., 'STU001', 'STU002').",
                },
            },
            "required": ["student_id"],
        },
    },
}
