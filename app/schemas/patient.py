from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

from app.models.patient import Gender

class PatientBase(BaseModel):
    name: str
    dob: Optional[date] = None
    gender: Optional[Gender] = None
    contact: Optional[str] = None
    photo: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[Gender] = None
    contact: Optional[str] = None
    photo: Optional[str] = None

class PatientResponse(PatientBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PatientListItem(BaseModel):
    id: str
    name: str
    gender: Optional[Gender] = None
    dob: Optional[date] = None
    contact: Optional[str] = None
    photo: Optional[str] = None
    relation: Optional[str] = None

    class Config:
        from_attributes = True

class PatientListResponse(BaseModel):
    patients: List[PatientListItem]
    total: int
