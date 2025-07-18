from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
import enum

from app.db.database import Base

class ReportType(str, enum.Enum):
    LAB_TEST = "lab_test"
    BLOOD_TEST = "blood_test"
    IMAGING = "imaging"
    PRESCRIPTION = "prescription"
    DISCHARGE_SUMMARY = "discharge_summary"
    VACCINATION = "vaccination"
    GROWTH_CHART = "growth_chart"
    NEWBORN_SCREENING = "newborn_screening"
    POST_DELIVERY = "post_delivery"
    LACTATION = "lactation"
    OTHER = "other"

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    report_type = Column(Enum(ReportType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient_mappings = relationship("PatientReportMapping", back_populates="report", cascade="all, delete-orphan")
    report_documents = relationship("ReportDocument", back_populates="report", cascade="all, delete-orphan")

class PatientReportMapping(Base):
    __tablename__ = "patient_report_mappings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(String, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="report_mappings")
    report = relationship("Report", back_populates="patient_mappings")

class ReportDocument(Base):
    __tablename__ = "report_documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    report_id = Column(String, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String, nullable=False)
    size = Column(Integer, nullable=True)
    link = Column(String, nullable=False)
    uploaded_by = Column(String, nullable=False)  # User ID who uploaded the document
    remark = Column(String, nullable=True)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    report = relationship("Report", back_populates="report_documents")
