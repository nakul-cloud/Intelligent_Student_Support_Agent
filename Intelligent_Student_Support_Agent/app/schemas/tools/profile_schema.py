"""Function schema for the student profile contact update tool.

Defines the JSON schema used by the Groq LLM to invoke update_student_profile.
"""

from typing import Any

UPDATE_STUDENT_PROFILE_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "update_student_profile",
        "description": (
            "Immediately updates the student's personal contact details (phone number, email address, "
            "or residential address) in the university database. Takes effect instantly without "
            "submitting a support ticket or waiting for administrative review."
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
            },
        },
    },
}
