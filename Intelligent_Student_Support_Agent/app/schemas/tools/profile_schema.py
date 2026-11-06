"""Function schema for the student profile contact update tool.

Defines the JSON schema used by the Groq LLM to invoke update_student_profile.
"""

from typing import Any

UPDATE_STUDENT_PROFILE_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "update_student_profile",
        "description": (
            "Updates the student's personal contact details (phone number, email address, "
            "or residential address) in the university database. Because modifying official student records "
            "is a sensitive operation, it enforces a Human-in-the-Loop approval gate. "
            "When first requested (or when confirmed is false), this tool initiates an approval request "
            "and requires explicit student confirmation (YES/NO). Only when the student has affirmatively "
            "confirmed should confirmed be set to true to commit changes to the database."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "The student's new phone or mobile number (e.g. '+91 98765 43210').",
                },
                "email": {
                    "type": "string",
                    "description": "The student's new contact email address.",
                },
                "address": {
                    "type": "string",
                    "description": "The student's new residential or hostel room address.",
                },
                "student_id": {
                    "type": "string",
                    "description": "The unique student ID whose profile is being updated (e.g., 'STU001').",
                },
                "confirmed": {
                    "type": "boolean",
                    "description": (
                        "Set to true ONLY if the student has explicitly and affirmatively replied YES, CONFIRM, "
                        "or APPROVED to proceed with this pending sensitive update. Defaults to false."
                    ),
                },
            },
        },
    },
}
