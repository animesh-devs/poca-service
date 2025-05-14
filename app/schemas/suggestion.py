from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class SuggestionBase(BaseModel):
    problem: str = Field(..., description="The medical problem or issue being addressed", min_length=3, max_length=200)
    description: Optional[str] = Field(None, description="Detailed description of the problem or suggestion")
    doctor_id: str = Field(..., description="ID of the doctor who created the suggestion")

class SuggestionCreate(SuggestionBase):
    """
    Schema for creating a new suggestion.

    Requires:
    - problem: A brief description of the medical issue
    - doctor_id: The ID of the doctor creating the suggestion

    Optional:
    - description: A more detailed explanation of the issue
    """
    @field_validator('problem')
    @classmethod
    def problem_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Problem cannot be empty')
        return v

class SuggestionUpdate(BaseModel):
    """
    Schema for updating an existing suggestion.

    Optional fields (at least one must be provided):
    - problem: A brief description of the medical issue
    - description: A more detailed explanation of the issue
    """
    problem: Optional[str] = Field(None, description="The medical problem or issue being addressed", min_length=3, max_length=200)
    description: Optional[str] = Field(None, description="Detailed description of the problem or suggestion")

class SuggestionFeedback(BaseModel):
    """
    Schema for providing feedback on a suggestion.

    Required:
    - feedback: The feedback text for the suggestion
    """
    feedback: str = Field(..., description="Feedback on the suggestion", min_length=3)

    @field_validator('feedback')
    @classmethod
    def feedback_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Feedback cannot be empty')
        return v

class SuggestionResponse(SuggestionBase):
    """
    Schema for the response when retrieving a suggestion.

    Includes all base fields plus:
    - id: Unique identifier for the suggestion
    - created_at: When the suggestion was created
    - has_feedback: Whether feedback has been provided
    - feedback: The feedback text (if any)
    - feedback_date: When feedback was provided (if any)
    """
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    has_feedback: bool = False
    feedback: Optional[str] = None
    feedback_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class SuggestionListItem(BaseModel):
    """
    Schema for a suggestion item in a list response.

    Contains a subset of fields for list display:
    - id: Unique identifier for the suggestion
    - problem: Brief description of the issue
    - doctor_id: ID of the doctor who created it
    - created_at: When it was created
    - has_feedback: Whether feedback has been provided
    """
    id: str
    problem: str
    doctor_id: str
    created_at: datetime
    has_feedback: bool = False

    class Config:
        from_attributes = True

class SuggestionListResponse(BaseModel):
    """
    Schema for the response when retrieving a list of suggestions.

    Contains:
    - suggestions: List of suggestion items
    - total: Total count of suggestions matching the query
    """
    suggestions: List[SuggestionListItem]
    total: int
