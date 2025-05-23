<<<<<<< HEAD
from typing import Callable
=======
from typing import Any, Callable, Dict
>>>>>>> 84e6feb9065367e96c9b9083f6e18e474d598f39
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import json
import logging
<<<<<<< HEAD
import traceback
=======

from app.utils.response import create_response
>>>>>>> 84e6feb9065367e96c9b9083f6e18e474d598f39

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
<<<<<<< HEAD
        """
        Process the request and standardize the response.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler

        Returns:
            A standardized response
        """
=======
>>>>>>> 84e6feb9065367e96c9b9083f6e18e474d598f39
        # Process the request and get the response
        response = await call_next(request)

        # Skip non-API routes
        if not request.url.path.startswith("/api") and not request.url.path == "/" and not request.url.path == "/health":
            return response

        # Only process JSON responses
<<<<<<< HEAD
        if not response.headers.get("content-type", "").startswith("application/json"):
=======
        if not isinstance(response, JSONResponse):
>>>>>>> 84e6feb9065367e96c9b9083f6e18e474d598f39
            return response

        # Check if the response is already in the standard format
        try:
<<<<<<< HEAD
            body = await response.body()
            content = json.loads(body)
=======
            content = json.loads(response.body.decode())
>>>>>>> 84e6feb9065367e96c9b9083f6e18e474d598f39

            # If it's already in the standard format, return it as is
            if isinstance(content, dict) and all(key in content for key in ["status_code", "status", "message", "data"]):
                return response

<<<<<<< HEAD
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
=======
            # For 204 No Content responses, create an empty success response
            if response.status_code == 204:
                wrapped_content = create_response(
                    data=None,
                    message="Operation completed successfully",
                    status_code=200,  # Change to 200 since we're adding content
                    success=True
                )
                return JSONResponse(
                    content=wrapped_content,
                    status_code=200,  # Use 200 instead of 204 since we have content now
                    headers=dict(response.headers),
                    media_type=response.media_type
                )

            # For error responses, format them properly
            if response.status_code >= 400:
                # If it's an error response with our error format
                if isinstance(content, dict) and "error_code" in content:
                    error_data = {
                        "error_code": content.get("error_code"),
                        "details": content.get("details", {})
                    }
                    wrapped_content = {
                        "status_code": response.status_code,
                        "status": False,
                        "message": content.get("message", "An error occurred"),
                        "data": error_data
                    }
                else:
                    # Generic error response
                    wrapped_content = {
                        "status_code": response.status_code,
                        "status": False,
                        "message": "An error occurred",
                        "data": {
                            "error_code": "SRV_001",
                            "details": content
                        }
                    }
            else:
                # For success responses, wrap the content
                wrapped_content = create_response(
                    data=content,
                    status_code=response.status_code,
                    success=True,
                    message="Operation completed successfully"
                )

            # Create a new response with the wrapped content
            return JSONResponse(
                content=wrapped_content,
                status_code=response.status_code if response.status_code != 204 else 200,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        except Exception as e:
            logger.error(f"Error in StandardResponseMiddleware: {str(e)}")
>>>>>>> 84e6feb9065367e96c9b9083f6e18e474d598f39
            # If there's an error processing the response, return it as is
            return response

def add_standard_response_middleware(app: FastAPI) -> None:
    """
    Add the StandardResponseMiddleware to the FastAPI application.

    Args:
        app: The FastAPI application
    """
    app.add_middleware(StandardResponseMiddleware)
