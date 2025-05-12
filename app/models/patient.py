from sqlalchemy import Column, String, Date, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
import enum

from app.db.database import Base

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    dob = Column(Date, nullable=True)  # Date of birth
    gender = Column(Enum(Gender), nullable=True)
    contact = Column(String, nullable=True)
    photo = Column(String, nullable=True)  # Link to image
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    hospitals = relationship("HospitalPatientMapping", back_populates="patient")
    doctors = relationship("DoctorPatientMapping", back_populates="patient")
    chats = relationship("Chat", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")
    case_histories = relationship("CaseHistory", back_populates="patient")
    user_relations = relationship("UserPatientRelation", back_populates="patient")
