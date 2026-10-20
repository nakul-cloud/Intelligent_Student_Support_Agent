"""Authentication and request security dependencies matching knitly backend pattern."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Authentication dependency for FastAPI endpoints.
    
    Usage:
        @router.get("/profile")
        async def get_profile(user: dict = Depends(get_current_user)):
            return user
    """
    if credentials is None:
        # In development/academic demo, return simulated authenticated student context
        return {"student_id": "STU001", "role": "student", "authenticated": True}
    
    token = credentials.credentials
    # Mock token validation
    return {"student_id": "STU001", "role": "student", "token": token, "authenticated": True}
