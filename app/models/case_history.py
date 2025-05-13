from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
import enum

from app.db.database import Base

class UploadedBy(str, enum.Enum):
    DOCTOR = "doctor"
    PATIENT = "patient"

class CaseHistory(Base):
    __tablename__ = "case_histories"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    summary = Column(String, nullable=True)
    documents = Column(JSON, nullable=True)  # JSON array of document IDs
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="case_histories")
    document_files = relationship("Document", back_populates="case_history", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    case_history_id = Column(String, ForeignKey("case_histories.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String, nullable=False)
    size = Column(Integer, nullable=True)
    link = Column(String, nullable=False)
    uploaded_by = Column(Enum(UploadedBy), nullable=False)
    remark = Column(String, nullable=True)  # Added remark field
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    case_history = relationship("CaseHistory", back_populates="document_files")
