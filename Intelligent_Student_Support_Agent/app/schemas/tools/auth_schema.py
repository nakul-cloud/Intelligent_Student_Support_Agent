"""Function schema for the student credential and password update tool.

Defines the JSON schema used by the Groq LLM to invoke update_student_password.
"""

from typing import Any

UPDATE_STUDENT_PASSWORD_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "update_student_password",
        "description": (
            "Immediately updates and changes the student's account password in the university database. "
            "Applies instantly to the database without administrative delays or support tickets. "
            "Invoke this whenever an authenticated student requests to change or update their account password "
            "and provides their desired new password."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "new_password": {
                    "type": "string",
                    "description": "The new plaintext password chosen by the student (must be at least 6 characters).",
                },
                "student_id": {
                    "type": "string",
                    "description": "The unique student ID whose password is being changed (e.g., 'STU001').",
                },
            },
            "required": ["new_password"],
        },
    },
}
