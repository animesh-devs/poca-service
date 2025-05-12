from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.appointment import AppointmentType, AppointmentStatus

class AppointmentBase(BaseModel):
    doctor_id: str
    patient_id: str
    hospital_id: Optional[str] = None
    time_slot: datetime
    type: AppointmentType
    extras: Optional[Dict[str, Any]] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    time_slot: Optional[datetime] = None
    type: Optional[AppointmentType] = None
    status: Optional[AppointmentStatus] = None
    extras: Optional[Dict[str, Any]] = None

class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus

class AppointmentCancellation(BaseModel):
    cancellation_reason: str

class AppointmentResponse(AppointmentBase):
    id: str
    status: AppointmentStatus
    cancelled_by: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class AppointmentListItem(BaseModel):
    id: str
    doctor_id: str
    patient_id: str
    hospital_id: Optional[str] = None
    time_slot: datetime
    type: AppointmentType
    status: AppointmentStatus
    
    class Config:
        from_attributes = True

class AppointmentListResponse(BaseModel):
    appointments: List[AppointmentListItem]
    total: int
