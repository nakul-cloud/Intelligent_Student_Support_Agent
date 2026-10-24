"""Security utilities for hashing and verifying passwords using bcrypt."""

import bcrypt
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
