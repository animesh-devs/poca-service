from typing import Any, Callable, Dict, Type, TypeVar, Generic, Optional
from fastapi import Response
from pydantic import BaseModel

from app.utils.response import create_response

T = TypeVar('T', bound=BaseModel)

def wrap_response(data: Any, response_model: Type[T] = None) -> Dict[str, Any]:
    """
    Wrap API response data in the standard response format.
    
    Args:
        data: The response data
        response_model: The Pydantic model to validate the response data against
        
    Returns:
        A dictionary with the standardized response format
    """
    # If the data is already in the standard format, return it as is
    if isinstance(data, dict) and all(key in data for key in ["status_code", "status", "message", "data"]):
        return data
    
    # Otherwise, wrap it in the standard format
    return create_response(data=data)
