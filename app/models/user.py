from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
import enum

from app.db.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"
    HOSPITAL = "hospital"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    role = Column(Enum(UserRole), nullable=False)
    contact = Column(String, nullable=True)
    address = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    profile_id = Column(String, nullable=True)  # Foreign key to doctor/patient/hospital profile
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient_relations = relationship("UserPatientRelation", back_populates="user")
