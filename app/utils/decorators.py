from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from fastapi import Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.utils.response import create_response

T = TypeVar("T", bound=Callable[..., Any])

def standardize_response(func: T) -> T:
    """
    Decorator to standardize API responses.
    
    This decorator wraps the response in the standard format:
    {
        "status_code": int,
        "status": bool,
        "message": str,
        "data": Any
    }
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Response:
        # Call the original function
        response = await func(*args, **kwargs)
        
        # If the response is already a Response object, return it as is
        if isinstance(response, Response):
            return response
            
        # Determine the appropriate message based on the status code
        status_code = kwargs.get("status_code", status.HTTP_200_OK)
        if status_code == status.HTTP_200_OK:
            message = "Request successful"
        elif status_code == status.HTTP_201_CREATED:
            message = "Resource created successfully"
        elif status_code == status.HTTP_202_ACCEPTED:
            message = "Request accepted for processing"
        elif status_code == status.HTTP_204_NO_CONTENT:
            message = "Operation completed successfully"
        else:
            message = "Operation completed successfully"
            
        # Create the standardized response
        wrapped_content = create_response(
            data=jsonable_encoder(response),
            status_code=status_code,
            success=status_code < 400,
            message=message
        )
        
        # Return the standardized response
        return JSONResponse(
            content=wrapped_content,
            status_code=status_code
        )
        
    return cast(T, wrapper)
