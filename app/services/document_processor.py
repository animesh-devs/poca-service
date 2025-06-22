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

# Try to import PDF processing libraries
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    try:
        import pypdf
        import PyPDF2
        PDF_AVAILABLE = True
    except ImportError:
        PDF_AVAILABLE = False

# Try to import image processing libraries
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

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
                # PDF files - extract text using PyPDF2
                if PDF_AVAILABLE:
                    try:
                        pdf_text = self._extract_pdf_text(file_content)
                        if pdf_text.strip():
                            logger.info(f"Successfully extracted {len(pdf_text)} characters from PDF {document_id}")
                            return pdf_text
                        else:
                            logger.warning(f"PDF {document_id} appears to be empty or contains no extractable text")
                            return f"[PDF Document: {metadata.get('filename', 'Unknown')} - No extractable text found]"
                    except Exception as e:
                        logger.error(f"Failed to extract text from PDF {document_id}: {e}")
                        return f"[PDF Document: {metadata.get('filename', 'Unknown')} - Text extraction failed: {str(e)}]"
                else:
                    logger.warning(f"PDF text extraction not available for {document_id} - PyPDF2 not installed")
                    return f"[PDF Document: {metadata.get('filename', 'Unknown')} - PyPDF2 library not available]"
            
            elif any(img_type in content_type for img_type in ["image/", "image/jpeg", "image/png", "image/gif"]) or \
                 any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
                # Image files - extract text using OCR
                if OCR_AVAILABLE:
                    try:
                        image_text = self._extract_image_text(file_content)
                        if image_text.strip():
                            logger.info(f"Successfully extracted {len(image_text)} characters from image {document_id}")
                            return image_text
                        else:
                            logger.warning(f"Image {document_id} appears to contain no readable text")
                            return f"[Image Document: {metadata.get('filename', 'Unknown')} - No readable text found]"
                    except Exception as e:
                        logger.error(f"Failed to extract text from image {document_id}: {e}")
                        return f"[Image Document: {metadata.get('filename', 'Unknown')} - OCR extraction failed: {str(e)}]"
                else:
                    logger.warning(f"OCR text extraction not available for {document_id} - pytesseract/PIL not installed")
                    return f"[Image Document: {metadata.get('filename', 'Unknown')} - OCR libraries not available]"
            
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

    def _extract_pdf_text(self, file_content: bytes) -> str:
        """
        Extract text from PDF file content

        Args:
            file_content: PDF file content as bytes

        Returns:
            str: Extracted text content
        """
        try:
            # Create a BytesIO object from the file content
            pdf_file = io.BytesIO(file_content)

            # Create PDF reader object
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # Extract text from all pages
            text_content = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text.strip():
                    text_content.append(page_text.strip())

            # Join all page text
            full_text = "\n\n".join(text_content)

            # Clean up the text (remove excessive whitespace, etc.)
            full_text = " ".join(full_text.split())

            return full_text

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise e

    def _extract_image_text(self, file_content: bytes) -> str:
        """
        Extract text from image file content using OCR

        Args:
            file_content: Image file content as bytes

        Returns:
            str: Extracted text content
        """
        try:
            # Create a BytesIO object from the file content
            image_file = io.BytesIO(file_content)

            # Open image with PIL
            image = Image.open(image_file)

            # Use pytesseract to extract text
            try:
                extracted_text = pytesseract.image_to_string(image)
            except pytesseract.TesseractNotFoundError:
                raise Exception("Tesseract OCR engine not installed. Please install tesseract-ocr system package.")
            except Exception as ocr_error:
                raise Exception(f"OCR processing failed: {str(ocr_error)}")

            # Clean up the text
            cleaned_text = " ".join(extracted_text.split())

            return cleaned_text

        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise e

    def _extract_pdf_text(self, file_content: bytes) -> str:
        """
        Extract text from PDF file content

        Args:
            file_content: PDF file content as bytes

        Returns:
            str: Extracted text content
        """
        try:
            # Create a BytesIO object from the file content
            pdf_file = io.BytesIO(file_content)

            # Create PDF reader object
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # Extract text from all pages
            text_content = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text.strip():
                    text_content.append(page_text.strip())

            # Join all page text
            full_text = "\n\n".join(text_content)

            # Clean up the text (remove excessive whitespace, etc.)
            full_text = " ".join(full_text.split())

            return full_text

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise e
    
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
