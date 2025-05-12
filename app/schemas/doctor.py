from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, time

class DoctorBase(BaseModel):
    name: str
    photo: Optional[str] = None
    designation: Optional[str] = None
    experience: Optional[int] = None
    details: Optional[str] = None
    contact: Optional[str] = None
    shift_time_start: Optional[time] = None
    shift_time_end: Optional[time] = None

class DoctorCreate(DoctorBase):
    pass

class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    photo: Optional[str] = None
    designation: Optional[str] = None
    experience: Optional[int] = None
    details: Optional[str] = None
    contact: Optional[str] = None
    shift_time_start: Optional[time] = None
    shift_time_end: Optional[time] = None

class DoctorResponse(DoctorBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DoctorListItem(BaseModel):
    id: str
    name: str
    designation: Optional[str] = None
    experience: Optional[int] = None
    photo: Optional[str] = None
    chat_id: Optional[str] = None
    is_active_chat: Optional[bool] = None
    
    class Config:
        from_attributes = True

class DoctorListResponse(BaseModel):
    doctors: List[DoctorListItem]
    total: int
