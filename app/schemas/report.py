from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.models.report import ReportType

class ReportDocumentBase(BaseModel):
    file_name: str
    size: Optional[int] = None
    link: str
    uploaded_by: str
    remark: Optional[str] = None

class ReportDocumentCreate(ReportDocumentBase):
    report_id: str

class ReportDocumentResponse(ReportDocumentBase):
    id: str
    report_id: str
    upload_timestamp: datetime
    created_at: datetime
    download_link: Optional[str] = None  # Dynamically generated download link

    model_config = {
        "from_attributes": True
    }

class PatientReportMappingBase(BaseModel):
    patient_id: str
    report_id: str

class PatientReportMappingCreate(PatientReportMappingBase):
    pass

class PatientReportMappingResponse(PatientReportMappingBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

class ReportBase(BaseModel):
    title: str
    description: Optional[str] = None
    report_type: ReportType

class ReportCreate(ReportBase):
    patient_id: str  # Used to create the mapping
    document_ids: Optional[List[str]] = None  # List of pre-uploaded document IDs

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    report_type: Optional[ReportType] = None

class ReportResponse(ReportBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    report_documents: Optional[List[ReportDocumentResponse]] = None

    model_config = {
        "from_attributes": True
    }

class ReportListItem(BaseModel):
    id: str
    title: str
    report_type: ReportType
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class ReportListResponse(BaseModel):
    reports: List[ReportListItem]
    total: int
