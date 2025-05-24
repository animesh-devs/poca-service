from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.models.case_history import UploadedBy

class DocumentBase(BaseModel):
    file_name: str
    size: Optional[int] = None
    link: str
    uploaded_by: UploadedBy
    remark: Optional[str] = None

class DocumentCreate(DocumentBase):
    case_history_id: str

class DocumentResponse(DocumentBase):
    id: str
    case_history_id: str
    upload_timestamp: datetime
    created_at: datetime
    download_link: Optional[str] = None  # Dynamically generated download link

    class Config:
        from_attributes = True

class CaseHistoryBase(BaseModel):
    patient_id: str
    summary: Optional[str] = None
    documents: Optional[List[str]] = None  # List of document IDs

class CaseHistoryCreate(CaseHistoryBase):
    pass

class CaseHistoryUpdate(BaseModel):
    summary: Optional[str] = None
    documents: Optional[List[str]] = None  # List of document IDs

class CaseHistoryResponse(CaseHistoryBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    document_files: Optional[List[DocumentResponse]] = None

    class Config:
        from_attributes = True
