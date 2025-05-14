from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.chat import MessageType

class ChatBase(BaseModel):
    doctor_id: str
    patient_id: str
    is_active_for_doctor: bool = True
    is_active_for_patient: bool = True

class ChatCreate(ChatBase):
    pass

class ChatResponse(ChatBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

class ChatListItem(BaseModel):
    id: str
    doctor_id: str
    patient_id: str
    is_active_for_doctor: bool
    is_active_for_patient: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class ChatListResponse(BaseModel):
    chats: List[ChatListItem]
    total: int

class MessageBase(BaseModel):
    chat_id: str
    sender_id: str
    receiver_id: str
    message: str
    message_type: MessageType = MessageType.TEXT
    file_details: Optional[Dict[str, Any]] = None

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: str
    timestamp: datetime
    is_read: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class MessageListItem(BaseModel):
    id: str
    chat_id: str
    sender_id: str
    receiver_id: str
    message: str
    message_type: MessageType
    file_details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    is_read: bool

    model_config = {
        "from_attributes": True
    }

class MessageListResponse(BaseModel):
    messages: List[MessageListItem]
    total: int

class ReadStatusUpdate(BaseModel):
    message_id: Optional[str] = None
    message_ids: Optional[List[str]] = None
    is_read: bool = True

    model_config = {
        "extra": "allow"
    }
