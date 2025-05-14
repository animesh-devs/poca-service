from sqlalchemy import Column, String, Integer, DateTime, Time, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.db.database import Base
from app.models.user import User

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    photo = Column(String, nullable=True)  # Link to image
    designation = Column(String, nullable=True)
    experience = Column(Integer, nullable=True)  # Years of experience
    details = Column(String, nullable=True)  # Education, achievements, etc.
    contact = Column(String, nullable=True)
    shift_time_start = Column(Time, nullable=True)
    shift_time_end = Column(Time, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="doctor_profile")
    hospitals = relationship("HospitalDoctorMapping", back_populates="doctor")
    patients = relationship("DoctorPatientMapping", back_populates="doctor")
    chats = relationship("Chat", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")
    suggestions = relationship("Suggestion", back_populates="doctor")
