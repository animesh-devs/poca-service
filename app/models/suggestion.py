from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
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
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Feedback fields
    has_feedback = Column(Boolean, default=False)
    feedback = Column(Text, nullable=True)
    feedback_date = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    doctor = relationship("Doctor", back_populates="suggestions")
