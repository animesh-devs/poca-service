from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.db.database import Base

class Hospital(Base):
    __tablename__ = "hospitals"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    contact = Column(String, nullable=True)
    pin_code = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=False)
    specialities = Column(JSON, nullable=True)  # JSON array of specialities
    link = Column(String, nullable=True)
    website = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    doctors = relationship("HospitalDoctorMapping", back_populates="hospital")
    patients = relationship("HospitalPatientMapping", back_populates="hospital")
    appointments = relationship("Appointment", back_populates="hospital")
