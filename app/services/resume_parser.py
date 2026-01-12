import pdfplumber
from fastapi import UploadFile, HTTPException
import io


class ResumeParser:
    """Service to parse PDF resumes and extract text"""
    
    @staticmethod
    async def extract_text_from_pdf(file: UploadFile) -> str:
        """
        Extract text from uploaded PDF file
        
        Args:
            file: UploadFile object containing the PDF
            
        Returns:
            str: Extracted text from PDF
            
        Raises:
            HTTPException: If PDF is invalid, empty, or cannot be processed
        """
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Only PDF files are accepted."
            )
        
        try:
            # Read file content
            content = await file.read()
            
            if len(content) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded PDF file is empty."
                )
            
            # Extract text using pdfplumber
            text = ""
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                if len(pdf.pages) == 0:
                    raise HTTPException(
                        status_code=400,
                        detail="PDF contains no pages."
                    )
                
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # Check if any text was extracted
            if not text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract text from PDF. The file might be scanned or image-based."
                )
            
            # Clean and normalize text
            text = ResumeParser._clean_text(text)
            
            return text
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing PDF: {str(e)}"
            )
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            str: Cleaned text
        """
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        
        # Join with single newline
        cleaned_text = '\n'.join(lines)
        
        return cleaned_text