from typing import Any, Dict, Optional
from fastapi import status

def create_response(
    data: Any = None,
    message: str = "successful",
    status_code: int = status.HTTP_200_OK,
    success: bool = True
) -> Dict[str, Any]:
    """
    Create a standardized API response.
    
    Args:
        data: The response data
        message: Human-readable message about the response
        status_code: HTTP status code
        success: Boolean indicating success or failure
        
    Returns:
        A dictionary with the standardized response format
    """
    return {
        "status_code": status_code,
        "status": success,
        "message": message,
        "data": data
    }
