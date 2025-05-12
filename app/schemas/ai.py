from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AISessionCreate(BaseModel):
    chat_id: str

class AISessionResponse(AISessionCreate):
    id: str
    start_timestamp: datetime
    end_timestamp: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

class AIMessageCreate(BaseModel):
    session_id: str
    message: str

class AIMessageResponse(AIMessageCreate):
    id: str
    response: Optional[str] = None
    is_summary: bool = False
    timestamp: datetime

    model_config = {
        "from_attributes": True
    }

class AIMessageListItem(BaseModel):
    id: str
    session_id: str
    message: str
    response: Optional[str] = None
    is_summary: bool = False
    timestamp: datetime

    model_config = {
        "from_attributes": True
    }

class AIMessageListResponse(BaseModel):
    messages: List[AIMessageListItem]
    total: int

class AISummaryUpdate(BaseModel):
    session_id: str
    summary: str

class AISummaryResponse(BaseModel):
    id: str
    session_id: str
    summary: str
    timestamp: datetime

    model_config = {
        "from_attributes": True
    }

class AISuggestedResponseRequest(BaseModel):
    session_id: str
    summary: str

class AISuggestedResponseResponse(BaseModel):
    id: str
    session_id: str
    suggested_response: str
    timestamp: datetime

    model_config = {
        "from_attributes": True
    }
