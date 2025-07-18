from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from app.models.patient import Gender
from app.models.mapping import RelationType

class PatientBase(BaseModel):
    name: str
    dob: Optional[date] = None
    gender: Optional[Gender] = None
    contact: Optional[str] = None
    photo: Optional[str] = None

    # Health information fields
    age: Optional[int] = None
    blood_group: Optional[str] = None
    height: Optional[int] = None  # Height in cm
    weight: Optional[int] = None  # Weight in kg
    medical_info: Optional[Dict[str, Any]] = None  # JSON object containing allergies, medications, conditions
    emergency_contact_name: Optional[str] = None
    emergency_contact_number: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[Gender] = None
    contact: Optional[str] = None
    photo: Optional[str] = None

    # Health information fields
    age: Optional[int] = None
    blood_group: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    medical_info: Optional[Dict[str, Any]] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_number: Optional[str] = None

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
    age: Optional[int] = None
    weight: Optional[int] = None

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
