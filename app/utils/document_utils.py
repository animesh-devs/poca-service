"""
Utility functions for document handling
"""
from typing import Dict, Any, List, Optional
from app.config import settings
from app.models.document import FileDocument
from app.models.case_history import Document as CaseHistoryDocument
from app.models.report import ReportDocument


def generate_download_link(document_id: str) -> str:
    """
    Generate a download link for a document
    
    Args:
        document_id: The unique document ID
        
    Returns:
        str: The complete download URL
    """
    return f"{settings.PUBLIC_BASE_URL}{settings.API_V1_PREFIX}/documents/{document_id}/download"


def enhance_case_history_document(document: CaseHistoryDocument) -> Dict[str, Any]:
    """
    Enhance a case history document with download link
    
    Args:
        document: CaseHistoryDocument instance
        
    Returns:
        Dict: Enhanced document data with download link
    """
    # Check if the document has a corresponding FileDocument entry
    # The link field in CaseHistoryDocument might contain the old format
    # We need to extract the document ID and generate a new link
    
    document_data = {
        "id": document.id,
        "case_history_id": document.case_history_id,
        "file_name": document.file_name,
        "size": document.size,
        "link": document.link,  # Keep original link
        "uploaded_by": document.uploaded_by,
        "remark": document.remark,
        "upload_timestamp": document.upload_timestamp,
        "created_at": document.created_at
    }
    
    # If the link contains our API structure, extract document ID and regenerate
    if "/documents/" in document.link and "/download" in document.link:
        try:
            # Extract document ID from the link
            parts = document.link.split("/documents/")
            if len(parts) > 1:
                doc_id_part = parts[1].split("/download")[0]
                # Generate new download link
                document_data["download_link"] = generate_download_link(doc_id_part)
            else:
                document_data["download_link"] = document.link
        except Exception:
            document_data["download_link"] = document.link
    else:
        document_data["download_link"] = document.link
    
    return document_data


def enhance_report_document(document: ReportDocument) -> Dict[str, Any]:
    """
    Enhance a report document with download link
    
    Args:
        document: ReportDocument instance
        
    Returns:
        Dict: Enhanced document data with download link
    """
    document_data = {
        "id": document.id,
        "report_id": document.report_id,
        "file_name": document.file_name,
        "size": document.size,
        "link": document.link,  # Keep original link
        "uploaded_by": document.uploaded_by,
        "remark": document.remark,
        "upload_timestamp": document.upload_timestamp,
        "created_at": document.created_at
    }
    
    # If the link contains our API structure, extract document ID and regenerate
    if "/documents/" in document.link and "/download" in document.link:
        try:
            # Extract document ID from the link
            parts = document.link.split("/documents/")
            if len(parts) > 1:
                doc_id_part = parts[1].split("/download")[0]
                # Generate new download link
                document_data["download_link"] = generate_download_link(doc_id_part)
            else:
                document_data["download_link"] = document.link
        except Exception:
            document_data["download_link"] = document.link
    else:
        document_data["download_link"] = document.link
    
    return document_data


def enhance_file_document(document: FileDocument) -> Dict[str, Any]:
    """
    Enhance a file document with download link
    
    Args:
        document: FileDocument instance
        
    Returns:
        Dict: Enhanced document data with download link
    """
    document_data = {
        "id": document.id,
        "file_name": document.file_name,
        "size": document.size,
        "link": document.link,  # Keep original link
        "document_type": document.document_type,
        "uploaded_by": document.uploaded_by,
        "uploaded_by_role": document.uploaded_by_role,
        "remark": document.remark,
        "entity_id": document.entity_id,
        "upload_timestamp": document.upload_timestamp,
        "created_at": document.created_at
    }
    
    # Generate download link using the document ID
    document_data["download_link"] = generate_download_link(document.id)
    
    return document_data


def enhance_message_file_details(file_details: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Enhance message file details with download link
    
    Args:
        file_details: Existing file details dictionary
        
    Returns:
        Dict: Enhanced file details with download link
    """
    if not file_details:
        return file_details
    
    enhanced_details = file_details.copy()
    
    # If document_id exists, generate download link
    if "document_id" in file_details:
        enhanced_details["download_link"] = generate_download_link(file_details["document_id"])
    
    return enhanced_details


def enhance_case_history_documents(documents: List[CaseHistoryDocument]) -> List[Dict[str, Any]]:
    """
    Enhance a list of case history documents with download links
    
    Args:
        documents: List of CaseHistoryDocument instances
        
    Returns:
        List[Dict]: List of enhanced document data with download links
    """
    return [enhance_case_history_document(doc) for doc in documents]


def enhance_report_documents(documents: List[ReportDocument]) -> List[Dict[str, Any]]:
    """
    Enhance a list of report documents with download links
    
    Args:
        documents: List of ReportDocument instances
        
    Returns:
        List[Dict]: List of enhanced document data with download links
    """
    return [enhance_report_document(doc) for doc in documents]


def enhance_file_documents(documents: List[FileDocument]) -> List[Dict[str, Any]]:
    """
    Enhance a list of file documents with download links
    
    Args:
        documents: List of FileDocument instances
        
    Returns:
        List[Dict]: List of enhanced document data with download links
    """
    return [enhance_file_document(doc) for doc in documents]
