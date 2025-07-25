from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from uuid import uuid4
import io

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.document import FileDocument, DocumentType, UploadedBy
from app.schemas.document import FileDocumentCreate, FileDocumentResponse, FileDocumentListResponse
from app.dependencies import get_current_user
from app.errors import create_error_response, ErrorCode
from app.services.document_storage import document_storage
# Removed document_access_control import - no longer using access control
from app.config import settings
from app.utils.decorators import standardize_response
from app.utils.document_utils import enhance_file_document
from app.dependencies import create_access_token
from datetime import timedelta
import secrets

router = APIRouter()

@router.post("/upload", response_model=FileDocumentResponse)
@standardize_response
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(DocumentType.OTHER),
    remark: Optional[str] = Form(None),
    entity_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Upload a document to in-memory storage and create a database record.

    The document is stored in memory and can be downloaded using the document ID.
    Access is controlled based on user roles and relationships.

    - **file**: The file to upload
    - **document_type**: The type of document (case_history, report, other)
    - **remark**: Optional remark about the document
    - **entity_id**: Optional ID of the entity to associate with (can be added later)
    """
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # Store document in memory storage
        storage_id = document_storage.store_document(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type
        )

        # Create downloadable link using the public base URL
        download_link = f"{settings.PUBLIC_BASE_URL}{settings.API_V1_PREFIX}/documents/{storage_id}/download"

        # Determine uploaded_by_role based on current user's role
        if current_user.role == UserRole.DOCTOR:
            uploaded_by_role = UploadedBy.DOCTOR
        elif current_user.role == UserRole.ADMIN:
            uploaded_by_role = UploadedBy.ADMIN
        else:
            uploaded_by_role = UploadedBy.PATIENT

        # Create document record in database
        db_document = FileDocument(
            id=storage_id,  # Use the storage ID as the document ID
            file_name=file.filename,
            size=file_size,
            link=download_link,
            document_type=document_type,
            uploaded_by=current_user.id,
            uploaded_by_role=uploaded_by_role,
            remark=remark,
            entity_id=entity_id
        )

        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        # Enhance document with download link
        enhanced_document = enhance_file_document(db_document)

        # Construct response
        return FileDocumentResponse(**enhanced_document)
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
@standardize_response
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get document metadata by ID - Open access for everyone
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

    # No access control - everyone can access document metadata

    # Enhance document with download link
    enhanced_document = enhance_file_document(document)

    return FileDocumentResponse(**enhanced_document)

@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Download a document by ID - Open access for everyone

    Returns the actual file content as a streaming response.
    No authentication or access control required.
    """
    # Get document metadata from database
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

    # No access control - everyone can download documents

    # Get document content from storage
    document_data = document_storage.get_document(document_id)
    if not document_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Document content not found in storage",
                error_code=ErrorCode.RES_001
            )
        )

    file_content, metadata = document_data

    # Create a streaming response
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=metadata.get("content_type", "application/octet-stream"),
        headers={
            "Content-Disposition": f"attachment; filename=\"{metadata.get('filename', 'download')}\""
        }
    )

@router.put("/{document_id}/link", response_model=FileDocumentResponse)
@standardize_response
async def link_document_to_entity(
    document_id: str,
    entity_id: str = Form(...),
    document_type: DocumentType = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Link a document to an entity (case history, report, etc.)
    Only the document uploader or admin can link documents.
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

    # Check if user can modify this document (only uploader or admin)
    if document.uploaded_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Access denied. Only the document uploader or admin can link documents.",
                error_code=ErrorCode.AUTH_003
            )
        )

    document.entity_id = entity_id
    document.document_type = document_type

    db.commit()
    db.refresh(document)

    # Enhance document with download link
    enhanced_document = enhance_file_document(document)

    return FileDocumentResponse(**enhanced_document)

@router.get("/storage/stats")
@standardize_response
async def get_storage_stats(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get storage statistics (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Access denied. Admin access required.",
                error_code=ErrorCode.AUTH_003
            )
        )

    stats = document_storage.get_storage_stats()
    return stats


# In-memory store for temporary download tokens (in production, use Redis)
temp_download_tokens = {}


@router.post("/{document_id}/download-token")
@standardize_response
async def create_download_token(
    document_id: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a temporary download token for a document - Open access for everyone

    This allows frontend applications to generate temporary download links
    that can be used in browsers without requiring Authorization headers.
    No authentication required.
    """
    # Check if document exists
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

    # No access control - everyone can create download tokens

    # Generate temporary token (valid for 1 hour)
    temp_token = secrets.token_urlsafe(32)

    # Store token with expiration (in production, use Redis with TTL)
    from datetime import datetime
    expiry = datetime.utcnow() + timedelta(hours=1)
    temp_download_tokens[temp_token] = {
        "document_id": document_id,
        "user_id": "anonymous",  # No user authentication required
        "expires_at": expiry
    }

    # Generate temporary download URL
    temp_download_url = f"{settings.PUBLIC_BASE_URL}{settings.API_V1_PREFIX}/documents/download-with-token?token={temp_token}"

    return {
        "download_token": temp_token,
        "download_url": temp_download_url,
        "expires_at": expiry.isoformat(),
        "expires_in_seconds": 3600
    }


@router.get("/download-with-token")
async def download_with_token(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Download a document using a temporary token

    This endpoint allows downloading documents without Authorization headers,
    making it suitable for direct browser downloads.
    """
    # Check if token exists and is valid
    if token not in temp_download_tokens:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired download token"
        )

    token_data = temp_download_tokens[token]

    # Check if token has expired
    from datetime import datetime
    if datetime.utcnow() > token_data["expires_at"]:
        # Clean up expired token
        del temp_download_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Download token has expired"
        )

    # Get document
    document_id = token_data["document_id"]
    document = db.query(FileDocument).filter(FileDocument.id == document_id).first()

    if not document:
        # Clean up token for non-existent document
        del temp_download_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Get file from storage
    try:
        document_data = document_storage.get_document(document_id)
        if not document_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File content not found in storage"
            )

        file_content, metadata = document_data

        # Create streaming response
        def generate():
            yield file_content

        # Clean up token after successful download (one-time use)
        del temp_download_tokens[token]

        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=metadata.get("content_type", "application/octet-stream"),
            headers={
                "Content-Disposition": f"attachment; filename=\"{metadata.get('filename', 'download')}\""
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving file: {str(e)}"
        )
