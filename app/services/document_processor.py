"""
Document processing service for extracting text from various document types
and generating AI-powered summaries
"""
import io
import logging
from typing import Optional, Dict, Any
import openai
from app.config import settings
from app.services.document_storage import document_storage

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for processing documents and generating summaries"""
    
    def __init__(self):
        """Initialize the document processor"""
        self.openai_api_key = settings.OPENAI_API_KEY
        self.openai_model = settings.OPENAI_MODEL
        
        if not self.openai_api_key:
            logger.warning("OpenAI API key not set. Document summarization will not work.")
    
    def extract_text_from_document(self, document_id: str) -> Optional[str]:
        """
        Extract text content from a document
        
        Args:
            document_id: The document ID to extract text from
            
        Returns:
            str: Extracted text content, or None if extraction fails
        """
        try:
            # Get document from storage
            document_data = document_storage.get_document(document_id)
            if not document_data:
                logger.error(f"Document {document_id} not found in storage")
                return None
            
            file_content, metadata = document_data
            content_type = metadata.get("content_type", "").lower()
            filename = metadata.get("filename", "").lower()
            
            # Handle different file types
            if "text/plain" in content_type or filename.endswith('.txt'):
                # Plain text files
                return file_content.decode('utf-8', errors='ignore')
            
            elif "application/pdf" in content_type or filename.endswith('.pdf'):
                # PDF files - would need PyPDF2 or similar library
                # For now, return a placeholder
                logger.warning(f"PDF text extraction not implemented for {document_id}")
                return f"[PDF Document: {metadata.get('filename', 'Unknown')} - Text extraction not available]"
            
            elif any(img_type in content_type for img_type in ["image/", "image/jpeg", "image/png", "image/gif"]) or \
                 any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
                # Image files - would need OCR (tesseract) for text extraction
                logger.warning(f"Image text extraction not implemented for {document_id}")
                return f"[Image Document: {metadata.get('filename', 'Unknown')} - OCR text extraction not available]"
            
            elif any(doc_type in content_type for doc_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]) or \
                 any(filename.endswith(ext) for ext in ['.doc', '.docx']):
                # Word documents - would need python-docx library
                logger.warning(f"Word document text extraction not implemented for {document_id}")
                return f"[Word Document: {metadata.get('filename', 'Unknown')} - Text extraction not available]"
            
            else:
                # Try to decode as text for other file types
                try:
                    return file_content.decode('utf-8', errors='ignore')
                except Exception as e:
                    logger.error(f"Failed to decode document {document_id} as text: {e}")
                    return f"[Document: {metadata.get('filename', 'Unknown')} - Text extraction failed]"
        
        except Exception as e:
            logger.error(f"Error extracting text from document {document_id}: {e}")
            return None
    
    async def generate_case_history_summary(self, document_ids: list, user_summary: str) -> str:
        """
        Generate a comprehensive case history summary using ChatGPT
        
        Args:
            document_ids: List of document IDs to analyze
            user_summary: User-provided summary text
            
        Returns:
            str: AI-generated comprehensive summary
        """
        try:
            if not self.openai_api_key or self.openai_api_key == "your_openai_api_key":
                logger.warning("OpenAI API key not set. Using mock summary.")
                return self._generate_mock_summary(document_ids, user_summary)
            
            # Extract text from all documents
            document_texts = []
            for doc_id in document_ids:
                text = self.extract_text_from_document(doc_id)
                if text:
                    document_texts.append(f"Document {doc_id}: {text[:1000]}...")  # Limit to first 1000 chars
            
            # Prepare the prompt for ChatGPT
            system_prompt = """
            You are a medical assistant helping to create comprehensive case history summaries.
            You will be provided with:
            1. A user-provided summary
            2. Text extracted from medical documents
            
            Your task is to create a short, crisp, and comprehensive case history summary that:
            - Combines information from both the user summary and document content
            - Highlights key medical information, symptoms, diagnoses, and treatments
            - Uses clear, professional medical language
            - Is concise but comprehensive (aim for 150-300 words)
            - Organizes information logically (chief complaint, history, findings, plan)
            
            Focus on medical relevance and accuracy. If documents contain non-medical content, ignore it.
            """
            
            user_content = f"""
            User-provided summary:
            {user_summary}
            
            Document content:
            {chr(10).join(document_texts) if document_texts else "No readable document content available"}
            
            Please generate a comprehensive case history summary based on this information.
            """
            
            # Call OpenAI API
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,  # Lower temperature for more consistent medical summaries
                max_tokens=500    # Limit response length
            )
            
            # Extract the response text
            ai_summary = response.choices[0].message.content.strip()
            logger.info(f"Generated AI case history summary: {ai_summary[:100]}...")
            
            return ai_summary
            
        except Exception as e:
            logger.error(f"Error generating case history summary: {e}")
            return f"Error generating AI summary: {str(e)}. Original summary: {user_summary}"
    
    def _generate_mock_summary(self, document_ids: list, user_summary: str) -> str:
        """Generate a mock summary when OpenAI is not available"""
        doc_count = len(document_ids)
        return f"""
        **Case History Summary (AI-Enhanced)**
        
        Based on the provided information and {doc_count} attached document(s):
        
        **Chief Complaint & History:**
        {user_summary}
        
        **Document Analysis:**
        {doc_count} medical document(s) have been reviewed and integrated into this summary.
        
        **Clinical Assessment:**
        This case requires comprehensive evaluation based on the documented history and attached medical records.
        
        **Recommendations:**
        Continue monitoring symptoms and follow up as clinically indicated.
        
        *Note: This is a mock summary. Enable OpenAI integration for AI-powered analysis.*
        """

# Global instance
document_processor = DocumentProcessor()
