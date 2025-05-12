from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.db.database import Base

class Suggestion(Base):
    __tablename__ = "suggestions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    problem = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    doctor_id = Column(String, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    doctor = relationship("Doctor", back_populates="suggestions")
