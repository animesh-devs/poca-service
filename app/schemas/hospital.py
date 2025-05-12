from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime

class HospitalBase(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    contact: Optional[str] = None
    pin_code: Optional[str] = None
    email: EmailStr
    specialities: Optional[List[str]] = None
    link: Optional[str] = None
    website: Optional[str] = None

class HospitalCreate(HospitalBase):
    pass

class HospitalUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    contact: Optional[str] = None
    pin_code: Optional[str] = None
    specialities: Optional[List[str]] = None
    link: Optional[str] = None
    website: Optional[str] = None

class HospitalResponse(HospitalBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class HospitalListItem(BaseModel):
    id: str
    name: str
    city: Optional[str] = None
    state: Optional[str] = None
    specialities: Optional[List[str]] = None
    
    class Config:
        from_attributes = True

class HospitalListResponse(BaseModel):
    hospitals: List[HospitalListItem]
    total: int
