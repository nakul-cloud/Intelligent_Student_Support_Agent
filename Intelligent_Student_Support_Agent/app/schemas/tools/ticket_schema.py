"""Function schema for the administrative support ticketing tool.

Defines the JSON schema used by the Groq LLM to decide when and how
to invoke the create_support_ticket tool.
"""

from typing import Any

TICKET_TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "create_support_ticket",
        "description": (
            "Create a formal administrative support ticket for escalating student requests, "
            "fee extension requests, attendance condonation appeals, or technical grievances. "
            "Generates a unique tracking ID (e.g. TICK-12345) and records the ticket in PostgreSQL."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "The unique student ID creating the ticket (e.g., 'STU001').",
                },
                "category": {
                    "type": "string",
                    "description": (
                        "The category of the request (e.g., 'Fee Installment Extension', "
                        "'Attendance Condonation', 'Grade Dispute Appeal', 'IT Facilities', 'General Grievance')."
                    ),
                },
                "description": {
                    "type": "string",
                    "description": "Detailed explanation of the student's issue, reason, and requested action.",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "Urgency level of the request. Defaults to 'medium'.",
                },
            },
            "required": ["student_id", "category", "description"],
        },
    },
}
