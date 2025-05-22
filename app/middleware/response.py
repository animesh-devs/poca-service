from typing import Any, Callable, Dict
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import json

from app.utils.response import create_response

class StandardResponseMiddleware(BaseHTTPMiddleware):
    """
    Middleware to standardize API responses.

    This middleware wraps all API responses in the standard format:
    {
        "status_code": int,
        "status": bool,
        "message": str,
        "data": Any
    }
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Process the request and get the response
        response = await call_next(request)

        # Only process JSON responses
        if not isinstance(response, JSONResponse):
            return response

        # Check if the response is already in the standard format
        try:
            content = json.loads(response.body.decode())
            if isinstance(content, dict) and all(key in content for key in ["status_code", "status", "message", "data"]):
                # Response is already in the standard format
                return response
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Not a valid JSON response or not decodable
            return response

        # Wrap the response in the standard format
        wrapped_content = create_response(
            data=content,
            status_code=response.status_code
        )

        # Create a new response with the wrapped content
        return JSONResponse(
            content=wrapped_content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )

def add_standard_response_middleware(app: FastAPI) -> None:
    """
    Add the StandardResponseMiddleware to the FastAPI application.

    Args:
        app: The FastAPI application
    """
    app.add_middleware(StandardResponseMiddleware)
