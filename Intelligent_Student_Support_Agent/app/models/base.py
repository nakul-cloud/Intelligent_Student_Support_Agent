"""Master SQLAlchemy declarative base and reusable mixins.

Follows enterprise clean architecture standards.
Provides enterprise UUID primary keys and timezone-aware timestamps across all tables.
"""

import uuid
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Master Base class for all SQLAlchemy ORM models."""

    pass


class UUIDMixin:
    """Mixin providing standardized UUID primary key.
    
    Prevents sequential enumeration attacks and conforms to enterprise standards.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, index=True, sort_order=-1
    )


class TimestampMixin:
    """Mixin providing created_at and updated_at tracking with server defaults."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        sort_order=9998,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        sort_order=9999,
    )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """Abstract base model combining UUID primary key and audit timestamps."""

    __abstract__ = True
