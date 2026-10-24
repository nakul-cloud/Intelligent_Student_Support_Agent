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

GET_TICKET_STATUS_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_ticket_status",
        "description": (
            "Lookup and check the current status, resolution progress, and details of an existing "
            "support ticket using its reference ID (e.g., 'TICK-96628'). Invoke this whenever "
            "a student asks about the update, status, or details of a specific ticket."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "The ticket tracking reference ID (e.g. 'TICK-96628').",
                },
                "student_id": {
                    "type": "string",
                    "description": "The unique student ID owning the ticket (e.g., 'STU001').",
                },
            },
            "required": ["ticket_id"],
        },
    },
}

LIST_STUDENT_TICKETS_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "list_student_tickets",
        "description": (
            "Retrieve and list all support tickets previously filed by the authenticated student. "
            "Invoke this when a student asks to see all their tickets, open grievances, or check "
            "tickets without knowing their exact ticket ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "The unique student ID whose tickets should be retrieved (e.g., 'STU001').",
                },
            },
            "required": ["student_id"],
        },
    },
}

