from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from uuid import uuid4

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.document import FileDocument, DocumentType, UploadedBy
from app.schemas.document import FileDocumentCreate, FileDocumentResponse, FileDocumentListResponse
from app.dependencies import get_current_user
from app.errors import create_error_response, ErrorCode

router = APIRouter()

@router.post("/upload", response_model=FileDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(DocumentType.OTHER),
    remark: Optional[str] = Form(None),
    entity_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Upload a document that can later be associated with a case history, report, or other entity.
    
    This endpoint allows uploading a document without requiring a specific entity ID first,
    solving the cyclic dependency between document creation and entity creation.
    
    - **file**: The file to upload
    - **document_type**: The type of document (case_history, report, other)
    - **remark**: Optional remark about the document
    - **entity_id**: Optional ID of the entity to associate with (can be added later)
    """
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # In a real application, you would upload this file to a storage service
        # and get a link to the uploaded file. For this example, we'll create a dummy link.
        file_link = f"https://example.com/files/{uuid4()}/{file.filename}"

        # Determine uploaded_by_role based on current user's role
        if current_user.role == UserRole.DOCTOR:
            uploaded_by_role = UploadedBy.DOCTOR
        elif current_user.role == UserRole.ADMIN:
            uploaded_by_role = UploadedBy.ADMIN
        else:
            uploaded_by_role = UploadedBy.PATIENT

        # Create document
        db_document = FileDocument(
            file_name=file.filename,
            size=file_size,
            link=file_link,
            document_type=document_type,
            uploaded_by=current_user.id,
            uploaded_by_role=uploaded_by_role,
            remark=remark,
            entity_id=entity_id
        )

        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        # Construct response
        return FileDocumentResponse(
            id=db_document.id,
            file_name=db_document.file_name,
            size=db_document.size,
            link=db_document.link,
            document_type=db_document.document_type,
            uploaded_by=db_document.uploaded_by,
            uploaded_by_role=db_document.uploaded_by_role,
            remark=db_document.remark,
            entity_id=db_document.entity_id,
            upload_timestamp=db_document.upload_timestamp,
            created_at=db_document.created_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"An error occurred: {str(e)}",
                error_code=ErrorCode.SRV_001
            )
        )

@router.get("/{document_id}", response_model=FileDocumentResponse)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a document by ID
    """
    document = db.query(FileDocument).filter(FileDocument.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Document not found",
                error_code=ErrorCode.RES_001
            )
        )
    
    return document

@router.put("/{document_id}/link", response_model=FileDocumentResponse)
async def link_document_to_entity(
    document_id: str,
    entity_id: str = Form(...),
    document_type: DocumentType = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Link a document to an entity (case history, report, etc.)
    """
    document = db.query(FileDocument).filter(FileDocument.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Document not found",
                error_code=ErrorCode.RES_001
            )
        )
    
    document.entity_id = entity_id
    document.document_type = document_type
    
    db.commit()
    db.refresh(document)
    
    return document
