"""Authentication and request security dependencies.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for extracting and validating
  Bearer JWT tokens from HTTP request headers.
- Dependency Inversion (DIP): Injected via FastAPI Depends into protected endpoints.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.exceptions.custom_exceptions import AuthenticationError
from app.services.auth_service import decode_access_token
from app.utils.logger import logger

security = HTTPBearer(auto_error=False)


async def get_current_student(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """FastAPI dependency extracting and validating Bearer JWT, returning student_id.

    Raises:
        HTTPException: 401 Unauthorized if token is missing, expired, or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        student_id = decode_access_token(token)
        return student_id
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as exc:
        logger.warning(f"Unexpected error validating token: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    student_id: str = Depends(get_current_student),
) -> dict:
    """Backward-compatible student context dictionary dependency."""
    return {
        "student_id": student_id,
        "role": "student",
        "authenticated": True,
    }
