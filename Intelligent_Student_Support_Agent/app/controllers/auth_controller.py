"""Controller orchestrating student authentication requests and responses.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Validates HTTP payloads and maps service results to standard API responses.
- Dependency Inversion (DIP): Injects AsyncSession into AuthService.
"""

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth_schema import ChangePasswordRequest, LoginRequest, SignupRequest
from app.services.auth_service import AuthService
from app.utils.response import success_response


class AuthController:
    """Controller handling student signup, login, and identity verification."""

    @staticmethod
    async def signup(request: SignupRequest, session: AsyncSession):
        """Enrolls a student with authentication credentials."""
        service = AuthService(session)
        result = await service.signup(request)
        return success_response(
            status_code=status.HTTP_201_CREATED,
            message="Student account registered successfully.",
            data=result,
        )

    @staticmethod
    async def login(request: LoginRequest, session: AsyncSession):
        """Authenticates student credentials and issues a JWT access token."""
        service = AuthService(session)
        token_response = await service.login(request)
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Authentication successful.",
            data=token_response.model_dump(),
        )

    @staticmethod
    async def change_password(
        student_id: str,
        request: ChangePasswordRequest,
        session: AsyncSession,
    ):
        """Updates the password for an authenticated student."""
        service = AuthService(session)
        result = await service.change_password(student_id, request.new_password)
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Password updated successfully.",
            data=result,
        )

