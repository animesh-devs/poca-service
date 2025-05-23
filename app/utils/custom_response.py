from typing import Any, Dict, Optional, TypeVar, Generic
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.utils.response import create_response

T = TypeVar('T')

def convert_to_dict(obj: Any) -> Any:
    """
    Convert an object to a JSON-serializable dictionary.

    Args:
        obj: The object to convert

    Returns:
        A JSON-serializable representation of the object
    """
    if hasattr(obj, "model_dump"):
        # If it's a Pydantic model, use model_dump
        return obj.model_dump()
    elif hasattr(obj, "__dict__") and not isinstance(obj, type):
        # For SQLAlchemy models and other objects with __dict__
        result = {}
        for key, value in obj.__dict__.items():
            # Skip private attributes and SQLAlchemy state
            if not key.startswith('_'):
                result[key] = convert_to_dict(value)
        return result
    elif isinstance(obj, list):
        # For lists, convert each item
        return [convert_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        # For dictionaries, convert each value
        return {key: convert_to_dict(value) for key, value in obj.items()}
    else:
        # For primitive types, return as is
        return obj

class StandardJSONResponse(JSONResponse, Generic[T]):
    """
    A custom JSONResponse that automatically wraps the response data in the standard format.

    This class is used to ensure that all API responses follow the standard format:
    {
        "status_code": int,
        "status": bool,
        "message": str,
        "data": Any
    }
    """

    def __init__(
        self,
        content: Any = None,
        status_code: int = status.HTTP_200_OK,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
        background: Optional[Any] = None,
        message: str = None,
    ):
        # Determine an appropriate message based on the status code if not provided
        if message is None:
            if status_code == 200:
                message = "Request successful"
            elif status_code == 201:
                message = "Resource created successfully"
            elif status_code == 202:
                message = "Request accepted for processing"
            elif status_code == 204:
                message = "Operation completed successfully"
            elif status_code >= 400:
                message = "An error occurred"
            else:
                message = "Operation completed successfully"

        # Determine success based on status code
        success = status_code < 400

        # Convert content to a JSON-serializable format
        serializable_content = convert_to_dict(content)

        # Create the standardized response
        wrapped_content = create_response(
            data=serializable_content,
            message=message,
            status_code=status_code,
            success=success
        )

        # Use 200 instead of 204 since we're adding content
        if status_code == 204:
            status_code = 200

        # Initialize the parent JSONResponse with the wrapped content
        super().__init__(
            content=wrapped_content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background
        )
