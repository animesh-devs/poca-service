from typing import Callable
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import json
import logging
import traceback

logger = logging.getLogger(__name__)

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
        """
        Process the request and standardize the response.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler

        Returns:
            A standardized response
        """
        # Process the request and get the response
        response = await call_next(request)

        # Skip non-API routes
        if not request.url.path.startswith("/api") and not request.url.path == "/" and not request.url.path == "/health":
            return response

        # Only process JSON responses
        if not response.headers.get("content-type", "").startswith("application/json"):
            return response

        # Check if the response is already in the standard format
        try:
            body = await response.body()
            content = json.loads(body)

            # If it's already in the standard format, return it as is
            if isinstance(content, dict) and all(key in content for key in ["status_code", "status", "message", "data"]):
                return response

            # Determine the appropriate message based on the status code
            if response.status_code == 200:
                message = "Request successful"
            elif response.status_code == 201:
                message = "Resource created successfully"
            elif response.status_code == 202:
                message = "Request accepted for processing"
            elif response.status_code == 204:
                message = "Operation completed successfully"
            else:
                message = "Operation completed successfully"

            # Create the standardized response
            wrapped_content = {
                "status_code": response.status_code,
                "status": response.status_code < 400,
                "message": message,
                "data": content
            }

            # Return the standardized response
            return JSONResponse(
                content=wrapped_content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json"
            )
        except Exception as e:
            logger.error(f"Error in StandardResponseMiddleware: {str(e)}")
            logger.error(traceback.format_exc())
            # If there's an error processing the response, return it as is
            return response

def add_standard_response_middleware(app: FastAPI) -> None:
    """
    Add the StandardResponseMiddleware to the FastAPI application.

    Args:
        app: The FastAPI application
    """
    app.add_middleware(StandardResponseMiddleware)
