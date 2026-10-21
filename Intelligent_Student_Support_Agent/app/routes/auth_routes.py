"""FastAPI route endpoints for student authentication and token issuance.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Routes HTTP requests for /api/auth to the appropriate controller methods.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.controllers.auth_controller import AuthController
from app.middlewares.auth import get_current_student
from app.schemas.auth_schema import LoginRequest, SignupRequest
from app.utils.response import success_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    summary="Register student credentials",
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    request: SignupRequest,
    session: AsyncSession = Depends(get_db),
):
    """Enrolls an existing university student with account credentials."""
    return await AuthController.signup(request, session)


@router.post(
    "/login",
    summary="Authenticate student and obtain JWT",
    status_code=status.HTTP_200_OK,
)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db),
):
    """Authenticates credentials and returns a 24-hour signed JWT access token."""
    return await AuthController.login(request, session)


@router.get(
    "/me",
    summary="Verify current authenticated student token",
    status_code=status.HTTP_200_OK,
)
async def get_me(
    student_id: str = Depends(get_current_student),
):
    """Protected endpoint verifying current JWT token and returning authenticated student_id."""
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Token is valid.",
        data={"student_id": student_id, "authenticated": True},
    )
