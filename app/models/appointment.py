from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
import enum

from app.db.database import Base

class AppointmentType(str, enum.Enum):
    REMOTE = "remote"
    REGULAR = "regular"
    EMERGENCY = "emergency"

class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    doctor_id = Column(String, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    hospital_id = Column(String, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=True)
    time_slot = Column(DateTime, nullable=False)
    type = Column(Enum(AppointmentType), nullable=False)
    status = Column(Enum(AppointmentStatus), nullable=False, default=AppointmentStatus.SCHEDULED)
    extras = Column(JSON, nullable=True)  # Additional appointment-specific information
    cancelled_by = Column(String, nullable=True)  # User ID who cancelled the appointment
    cancellation_reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")
    hospital = relationship("Hospital", back_populates="appointments")
