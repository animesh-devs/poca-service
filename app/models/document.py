from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
import enum

from app.db.database import Base

class DocumentType(str, enum.Enum):
    CASE_HISTORY = "case_history"
    REPORT = "report"
    OTHER = "other"

class UploadedBy(str, enum.Enum):
    DOCTOR = "doctor"
    PATIENT = "patient"
    ADMIN = "admin"

class FileDocument(Base):
    __tablename__ = "file_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    file_name = Column(String, nullable=False)
    size = Column(Integer, nullable=True)
    link = Column(String, nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False, default=DocumentType.OTHER)
    uploaded_by = Column(String, nullable=False)  # User ID who uploaded the document
    uploaded_by_role = Column(Enum(UploadedBy), nullable=False)
    remark = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)  # Optional ID of the entity this document is associated with
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
