"""Function schema for the official student handbook RAG retrieval tool.

Defines the JSON schema used by the Groq Llama 3.3 LLM to decide when and how
to invoke the search_student_handbook tool.
"""

from typing import Any

RAG_TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_student_handbook",
        "description": (
            "Search the official 44-page Student Handbook for university regulations, "
            "attendance requirements, grading systems, examination eligibility, "
            "academic misconduct, plagiarism rules, grievances, mobile phone policies, "
            "and committee procedures. Use this tool whenever the student asks about "
            "general university rules, minimum attendance (e.g. 70%), GPA calculations, "
            "or code of conduct."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The specific natural language question or topic to search for "
                        "(e.g., 'minimum attendance for end-term exams', 'grading system scale', "
                        "'ragging committee procedures')."
                    ),
                },
                "section_filter": {
                    "type": "string",
                    "description": (
                        "Optional section identifier to restrict the search to a specific policy "
                        "(e.g., '10.2', '10.3', '13.1', 'Annexure III'). Leave blank if searching broadly."
                    ),
                },
            },
            "required": ["query"],
        },
    },
}
