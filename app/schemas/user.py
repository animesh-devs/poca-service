from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from app.models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    role: UserRole
    contact: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True
    profile_id: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserListItem(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    role: UserRole
    is_active: bool
    profile_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    users: List[UserListItem]
    total: int
