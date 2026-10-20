"""Custom domain exceptions for Intelligent Student Support Agent."""

from typing import Any, Optional


class AppError(Exception):
    """Base application exception for handled operational errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        is_operational: bool = True,
        errors: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.is_operational = is_operational
        self.errors = errors


class ResourceNotFoundError(AppError):
    """Exception raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found", errors: Optional[Any] = None) -> None:
        super().__init__(message=message, status_code=404, errors=errors)


class ValidationError(AppError):
    """Exception raised for domain-level validation failures."""

    def __init__(self, message: str = "Validation error", errors: Optional[Any] = None) -> None:
        super().__init__(message=message, status_code=422, errors=errors)


class DatabaseConnectionError(AppError):
    """Exception raised when database operations fail."""

    def __init__(self, message: str = "Database operation failed", errors: Optional[Any] = None) -> None:
        super().__init__(message=message, status_code=503, errors=errors)


class VectorStoreError(AppError):
    """Exception raised when Qdrant vector operations fail."""

    def __init__(self, message: str = "Vector store operation failed", errors: Optional[Any] = None) -> None:
        super().__init__(message=message, status_code=503, errors=errors)
