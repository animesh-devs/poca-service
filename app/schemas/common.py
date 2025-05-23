from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field
from fastapi import status

T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    """
    Standard response model for all API endpoints.
    
    This model ensures that all API responses follow the standard format:
    {
        "status_code": int,
        "status": bool,
        "message": str,
        "data": Any
    }
    """
    status_code: int = Field(..., description="HTTP status code")
    status: bool = Field(..., description="Success status (true for 2xx, false otherwise)")
    message: str = Field(..., description="Human-readable message")
    data: Optional[T] = Field(None, description="Response data")
    
    @classmethod
    def success(cls, data: Any = None, message: str = "Request successful", status_code: int = status.HTTP_200_OK) -> "StandardResponse":
        """
        Create a success response.
        
        Args:
            data: The response data
            message: Human-readable message
            status_code: HTTP status code
            
        Returns:
            A StandardResponse instance with success status
        """
        return cls(
            status_code=status_code,
            status=True,
            message=message,
            data=data
        )
    
    @classmethod
    def error(cls, message: str = "An error occurred", status_code: int = status.HTTP_400_BAD_REQUEST, 
              error_code: str = None, details: Any = None) -> "StandardResponse":
        """
        Create an error response.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_code: Error code for client reference
            details: Additional error details
            
        Returns:
            A StandardResponse instance with error status
        """
        error_data = None
        if error_code or details is not None:
            error_data = {
                "error_code": error_code,
                "details": details
            }
            
        return cls(
            status_code=status_code,
            status=False,
            message=message,
            data=error_data
        )
