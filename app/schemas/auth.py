from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

from app.models.user import UserRole

class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    role: UserRole
    profile_id: Optional[str] = None

class Token(BaseModel):
    status_code: int = 200
    status: bool = True
    message: str = "successful"
    data: TokenData

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[datetime] = None
    type: Optional[str] = None

class RefreshToken(BaseModel):
    refresh_token: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None
    role: UserRole
    contact: Optional[str] = None
    address: Optional[str] = None

class AdminSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None
    contact: Optional[str] = None
    address: Optional[str] = None

class DoctorSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str
    contact: Optional[str] = None
    designation: Optional[str] = None
    experience: Optional[int] = None
    details: Optional[str] = None
    photo: Optional[str] = None

class PatientSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str
    dob: Optional[datetime] = None
    gender: Optional[str] = None
    contact: Optional[str] = None
    photo: Optional[str] = None
    age: Optional[int] = None
    blood_group: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    allergies: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    conditions: Optional[List[str]] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    address: Optional[str] = None

class HospitalSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    contact: Optional[str] = None
    pin_code: Optional[str] = None
    specialities: Optional[list] = None
    website: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ResetPassword(BaseModel):
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)
