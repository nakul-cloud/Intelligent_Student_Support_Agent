"""Pydantic schemas for the two-tier memory system.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively defines contracts for extracted facts
  and prompt-injection memory context formatting.
"""

from typing import List
from pydantic import BaseModel, Field


class ExtractedFact(BaseModel):
    """Represents a discrete verified fact extracted from student interactions."""

    fact_key: str = Field(..., description="Key identifier (e.g., programme, batch, preferred_name)")
    fact_value: str = Field(..., description="Extracted fact content")


class MemoryContextSchema(BaseModel):
    """Container for student memory facts to be formatted for agent system prompt."""

    student_id: str = Field(..., description="Student identifier")
    facts: List[ExtractedFact] = Field(default_factory=list, description="List of durable facts")

    def format_for_prompt(self) -> str:
        """Formats stored facts into a clean context string for system prompt injection.
        
        Returns:
            Human-readable memory summary or empty notice if no facts exist.
        """
        if not self.facts:
            return "No prior memory recorded for this student."

        formatted_lines = [
            f"- {fact.fact_key.replace('_', ' ').title()}: {fact.fact_value}"
            for fact in self.facts
        ]
        return "Student Profile Memory (Verified Facts):\n" + "\n".join(formatted_lines)
