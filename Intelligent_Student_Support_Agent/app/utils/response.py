"""Standard JSON response helpers for FastAPI controllers."""

from typing import Any, Optional
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(
    status_code: int = 200,
    message: str = "Success",
    data: Optional[Any] = None,
) -> JSONResponse:
    """Return a uniform success response structure.
    
    Format:
        {
            "status": "success",
            "message": "...",
            "data": ...
        }
    """
    payload = {
        "status": "success",
        "message": message,
        "data": data,
    }
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))


def error_response(
    status_code: int = 400,
    message: str = "Error",
    errors: Optional[Any] = None,
) -> JSONResponse:
    """Return a uniform error response structure.
    
    Format:
        {
            "status": "error" | "fail",
            "message": "...",
            "errors": ...
        }
    """
    status_text = "fail" if 400 <= status_code < 500 else "error"
    payload = {
        "status": status_text,
        "message": message,
        "errors": errors,
    }
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))
