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
    request_id: Optional[str] = None,
) -> JSONResponse:
    """Return a uniform error response structure with optional correlation request ID.
    
    Format:
        {
            "status": "error" | "fail",
            "message": "...",
            "request_id": "...",
            "errors": ...
        }
    """
    status_text = "fail" if 400 <= status_code < 500 else "error"
    payload: dict[str, Any] = {
        "status": status_text,
        "message": message,
        "errors": errors,
    }
    if request_id:
        payload["request_id"] = request_id
        
    headers = {"X-Request-ID": request_id} if request_id else None
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload), headers=headers)
