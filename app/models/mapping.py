from sqlalchemy import Column, String, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
import enum

from app.db.database import Base

class RelationType(str, enum.Enum):
    SELF = "self"
    WIFE = "wife"
    HUSBAND = "husband"
    CHILD = "child"
    PARENT = "parent"
    OTHER = "other"

class HospitalDoctorMapping(Base):
    __tablename__ = "hospital_doctor_mappings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    hospital_id = Column(String, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(String, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    hospital = relationship("Hospital", back_populates="doctors")
    doctor = relationship("Doctor", back_populates="hospitals")

class HospitalPatientMapping(Base):
    __tablename__ = "hospital_patient_mappings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    hospital_id = Column(String, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    hospital = relationship("Hospital", back_populates="patients")
    patient = relationship("Patient", back_populates="hospitals")

class DoctorPatientMapping(Base):
    __tablename__ = "doctor_patient_mappings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    doctor_id = Column(String, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    doctor = relationship("Doctor", back_populates="patients")
    patient = relationship("Patient", back_populates="doctors")

class UserPatientRelation(Base):
    __tablename__ = "user_patient_relations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    relation = Column(Enum(RelationType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="patient_relations")
    patient = relationship("Patient", back_populates="user_relations")
