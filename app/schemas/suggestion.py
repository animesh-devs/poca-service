from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SuggestionBase(BaseModel):
    problem: str
    description: Optional[str] = None
    doctor_id: str

class SuggestionCreate(SuggestionBase):
    pass

class SuggestionUpdate(BaseModel):
    problem: Optional[str] = None
    description: Optional[str] = None

class SuggestionResponse(SuggestionBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SuggestionListItem(BaseModel):
    id: str
    problem: str
    doctor_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SuggestionListResponse(BaseModel):
    suggestions: List[SuggestionListItem]
    total: int
