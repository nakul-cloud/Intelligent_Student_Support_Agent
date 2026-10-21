"""Pydantic schemas for student authentication.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively defines data contracts and validation
  for authentication requests and responses.
"""

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    """Request payload for enrolling student credentials."""

    student_id: str = Field(
        ...,
        description="Enrolled student ID registered in the university system",
        examples=["STU001"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Password (minimum 8 characters)",
        examples=["Student@123"],
    )


class LoginRequest(BaseModel):
    """Request payload for student login."""

    student_id: str = Field(
        ...,
        description="Student ID",
        examples=["STU001"],
    )
    password: str = Field(
        ...,
        description="Account password",
        examples=["Student@123"],
    )


class TokenResponse(BaseModel):
    """Response payload containing JWT bearer token."""

    access_token: str = Field(..., description="Signed JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry duration in seconds")


class TokenData(BaseModel):
    """Decoded JWT payload data contract."""

    student_id: str = Field(..., description="Authenticated student identifier")
