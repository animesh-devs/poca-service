from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date

from app.models.patient import Gender
from app.models.mapping import RelationType

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

class AdminPatientCreate(PatientBase):
    """Schema for admin to create a new patient with user details"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    user_name: str
    user_contact: Optional[str] = None
    relation_type: RelationType = RelationType.SELF
