"""Global exception handlers for FastAPI integration."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.exceptions.custom_exceptions import AppError
from app.utils.logger import logger
from app.utils.response import error_response


async def app_error_handler(request: Request, exc: AppError):
    """Handle custom application errors."""
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
    logger.warning(
        f"AppError on {request.method} {request.url.path} [req_id={request_id}]: {exc.message} (status: {exc.status_code})"
    )
    return error_response(
        status_code=exc.status_code,
        message=exc.message,
        errors=exc.errors,
        request_id=request_id,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle standard Starlette/FastAPI HTTP exceptions."""
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
    logger.warning(
        f"HTTPException on {request.method} {request.url.path} [req_id={request_id}]: {exc.detail} (status: {exc.status_code})"
    )
    return error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        errors=None,
        request_id=request_id,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request schema validation errors from Pydantic."""
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
    logger.warning(f"ValidationError on {request.method} {request.url.path} [req_id={request_id}]: {exc.errors()}")
    formatted_errors = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err.get("loc", []))
        formatted_errors.append({"field": field, "message": err.get("msg")})
    return error_response(
        status_code=422,
        message="Request payload validation failed",
        errors=formatted_errors,
        request_id=request_id,
    )


async def global_exception_handler(request: Request, exc: Exception):
    """Fallback handler for unhandled unexpected runtime exceptions."""
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
    logger.exception(f"Unhandled server error on {request.method} {request.url.path} [req_id={request_id}]: {str(exc)}")
    return error_response(
        status_code=500,
        message="An unexpected internal server error occurred",
        errors=str(exc),
        request_id=request_id,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application instance."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
