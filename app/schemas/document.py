from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.models.document import DocumentType, UploadedBy

class FileDocumentBase(BaseModel):
    file_name: str
    size: Optional[int] = None
    link: str
    document_type: DocumentType = DocumentType.OTHER
    uploaded_by: str
    uploaded_by_role: UploadedBy
    remark: Optional[str] = None
    entity_id: Optional[str] = None

class FileDocumentCreate(FileDocumentBase):
    pass

class FileDocumentResponse(FileDocumentBase):
    id: str
    upload_timestamp: datetime
    created_at: datetime
    download_link: Optional[str] = None  # Dynamically generated download link

    model_config = {
        "from_attributes": True
    }

class FileDocumentListResponse(BaseModel):
    documents: List[FileDocumentResponse]
    total: int
