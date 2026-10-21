"""SQLAlchemy model for student authentication credentials.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively models the auth_credentials persistence layer.
- Security-by-design: Stores only bcrypt hashed passwords, never plain text.
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class AuthCredentials(BaseModel):
    """Stores student authentication credentials with bcrypt hashed passwords."""

    __tablename__ = "auth_credentials"

    student_id: Mapped[str] = mapped_column(
        String, nullable=False, unique=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
