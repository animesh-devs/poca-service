"""
In-memory document storage service
Provides S3-like functionality for storing and retrieving documents
"""
import io
import mimetypes
from typing import Dict, Optional, Tuple
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

class DocumentStorage:
    """
    In-memory document storage service that mimics AWS S3 functionality
    """
    
    def __init__(self):
        # Dictionary to store documents: {document_id: (file_content, metadata)}
        self._storage: Dict[str, Tuple[bytes, Dict]] = {}
    
    def store_document(
        self, 
        file_content: bytes, 
        filename: str, 
        content_type: Optional[str] = None
    ) -> str:
        """
        Store a document in memory and return a unique document ID
        
        Args:
            file_content: The binary content of the file
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            str: Unique document ID
        """
        document_id = str(uuid4())
        
        # Auto-detect content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = "application/octet-stream"
        
        metadata = {
            "filename": filename,
            "content_type": content_type,
            "size": len(file_content),
            "document_id": document_id
        }
        
        self._storage[document_id] = (file_content, metadata)
        
        logger.info(f"Stored document {document_id} ({filename}, {len(file_content)} bytes)")
        return document_id
    
    def get_document(self, document_id: str) -> Optional[Tuple[bytes, Dict]]:
        """
        Retrieve a document by its ID
        
        Args:
            document_id: The unique document ID
            
        Returns:
            Tuple of (file_content, metadata) if found, None otherwise
        """
        return self._storage.get(document_id)
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from storage
        
        Args:
            document_id: The unique document ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        if document_id in self._storage:
            del self._storage[document_id]
            logger.info(f"Deleted document {document_id}")
            return True
        return False
    
    def document_exists(self, document_id: str) -> bool:
        """
        Check if a document exists in storage
        
        Args:
            document_id: The unique document ID
            
        Returns:
            bool: True if document exists, False otherwise
        """
        return document_id in self._storage
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict]:
        """
        Get metadata for a document without retrieving the content
        
        Args:
            document_id: The unique document ID
            
        Returns:
            Dict: Document metadata if found, None otherwise
        """
        if document_id in self._storage:
            return self._storage[document_id][1]
        return None
    
    def get_storage_stats(self) -> Dict:
        """
        Get storage statistics
        
        Returns:
            Dict: Storage statistics including total documents and total size
        """
        total_documents = len(self._storage)
        total_size = sum(len(content) for content, _ in self._storage.values())
        
        return {
            "total_documents": total_documents,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }

# Global instance of the document storage
document_storage = DocumentStorage()
