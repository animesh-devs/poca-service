from typing import TypeVar, Generic, Optional, Any, Dict
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar('T')

class StandardResponse(GenericModel, Generic[T]):
    """
    Standard API response format for all endpoints.
    
    Attributes:
        status_code: HTTP status code
        status: Boolean indicating success or failure
        message: Human-readable message about the response
        data: The actual response data (can be any type)
    """
    status_code: int = Field(200, description="HTTP status code")
    status: bool = Field(True, description="Success status")
    message: str = Field("successful", description="Response message")
    data: Optional[T] = Field(None, description="Response data")
