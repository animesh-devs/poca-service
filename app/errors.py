from enum import Enum
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Any, Dict, Optional

class ErrorCode(str, Enum):
    # Authentication errors
    AUTH_001 = "AUTH_001"  # Invalid credentials
    AUTH_002 = "AUTH_002"  # Token expired
    AUTH_003 = "AUTH_003"  # Invalid token
    AUTH_004 = "AUTH_004"  # Insufficient permissions
    AUTH_005 = "AUTH_005"  # Rate limit exceeded

    # Resource errors
    RES_001 = "RES_001"  # Resource not found
    RES_002 = "RES_002"  # Resource already exists
    RES_003 = "RES_003"  # Resource conflict

    # Validation errors
    VAL_001 = "VAL_001"  # Invalid input
    VAL_002 = "VAL_002"  # Missing required field

    # Server errors
    SRV_001 = "SRV_001"  # Internal server error
    SRV_002 = "SRV_002"  # Service unavailable

    # Business logic errors
    BIZ_001 = "BIZ_001"  # Operation not allowed
    BIZ_002 = "BIZ_002"  # Invalid operation

def create_error_response(
    status_code: int,
    message: str,
    error_code: ErrorCode,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a standardized error response"""
    return {
        "message": message,
        "error_code": error_code,
        "details": details or {}
    }

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    # Check if the detail is already a dict with our error format
    if isinstance(exc.detail, dict) and "message" in exc.detail and "error_code" in exc.detail:
        # Already in our format, use it directly
        error_data = {
            "error_code": exc.detail["error_code"],
            "details": exc.detail.get("details", {})
        }
    else:
        # Create a new error response
        error_data = {
            "error_code": getattr(exc, "error_code", ErrorCode.SRV_001),
            "details": getattr(exc, "details", {})
        }

    # Return the standardized response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "status": False,
            "message": str(exc.detail) if not isinstance(exc.detail, dict) else exc.detail.get("message", "An error occurred"),
            "data": error_data
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation exceptions"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "status": False,
            "message": "Validation error",
            "data": {
                "error_code": ErrorCode.VAL_001,
                "details": {"errors": exc.errors()}
            }
        }
    )
