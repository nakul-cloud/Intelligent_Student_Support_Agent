"""Authentication service layer handling user registration, password verification, and JWT lifecycle.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Encapsulates authentication and token generation logic.
- Open/Closed (OCP): Algorithms, token TTL, and signing keys are dynamically configured via settings.
- Dependency Inversion (DIP): Injects AsyncSession for testability and loose coupling.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.exceptions.custom_exceptions import (
    AuthenticationError,
    ConflictError,
    ResourceNotFoundError,
)
from app.models.auth_credentials import AuthCredentials
from app.models.student_records import Student
from app.schemas.auth_schema import LoginRequest, SignupRequest, TokenResponse
from app.utils.logger import logger


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt with salt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Safely verifies a candidate plaintext password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception as exc:
        logger.warning(f"Password verification encountered an error: {exc}")
        return False


def create_access_token(
    student_id: str, expires_delta: Optional[timedelta] = None
) -> str:
    """Creates a signed JSON Web Token for the authenticated student."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(hours=settings.jwt_expire_hours)

    payload = {
        "sub": student_id,
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """Decodes and validates a JWT access token, extracting the student_id claim.

    Raises:
        AuthenticationError: If token is expired, has an invalid signature, or is malformed.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        student_id: Optional[str] = payload.get("sub")
        if not student_id:
            raise AuthenticationError("Token payload missing student identifier claim ('sub')")
        return student_id
    except JWTError as exc:
        raise AuthenticationError(f"Invalid or expired access token: {str(exc)}")


class AuthService:
    """Orchestrates authentication operations including signup and credential validation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def signup(self, request: SignupRequest) -> Dict[str, Any]:
        """Registers credentials for an existing enrolled student (Option A).

        Raises:
            ResourceNotFoundError: If student_id is not enrolled in the university database.
            ConflictError: If credentials for this student_id already exist.
        """
        # 1. Enforce Option A: Verify student exists in enrolled database
        res_stu = await self.session.execute(
            select(Student).where(Student.student_id == request.student_id)
        )
        student = res_stu.scalar_one_or_none()
        if not student:
            raise ResourceNotFoundError(
                f"Student ID '{request.student_id}' is not enrolled in the university records. Registration prohibited."
            )

        # 2. Prevent duplicate account creation
        res_auth = await self.session.execute(
            select(AuthCredentials).where(
                AuthCredentials.student_id == request.student_id
            )
        )
        if res_auth.scalar_one_or_none():
            raise ConflictError(
                f"An account for student ID '{request.student_id}' already exists. Please log in."
            )

        # 3. Hash password and persist credentials
        hashed = hash_password(request.password)
        credentials = AuthCredentials(
            student_id=request.student_id,
            hashed_password=hashed,
        )
        self.session.add(credentials)
        await self.session.commit()

        logger.info(f"Student account created for: {request.student_id}")
        return {
            "student_id": request.student_id,
            "message": "Student account registered successfully.",
        }

    async def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticates student credentials and returns a signed bearer token.

        Raises:
            AuthenticationError: On invalid student_id or incorrect password.
        """
        res_auth = await self.session.execute(
            select(AuthCredentials).where(
                AuthCredentials.student_id == request.student_id
            )
        )
        credentials = res_auth.scalar_one_or_none()
        if not credentials:
            raise AuthenticationError("Invalid student ID or password.")

        if not verify_password(request.password, credentials.hashed_password):
            raise AuthenticationError("Invalid student ID or password.")

        token = create_access_token(request.student_id)
        expires_in = settings.jwt_expire_hours * 3600

        logger.info(f"Student successfully authenticated: {request.student_id}")
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
        )
