"""Function schema for the student scholarship awards and grants tool.

Defines the JSON schema used by the Groq Llama 3.3 LLM to decide when and how
to invoke the check_scholarship tool.
"""

from typing import Any

SCHOLARSHIP_TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "check_scholarship",
        "description": (
            "Check if a student has an active scholarship award, tuition fee waiver percentage, "
            "or semester grant allowance. Use this tool when a student asks about financial aid, "
            "scholarship renewals, or grant amounts."
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
