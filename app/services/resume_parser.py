import fitz  # PyMuPDF
from fastapi import UploadFile, HTTPException


class ResumeParser:
    """Service to parse PDF resumes and extract text - OPTIMIZED with PyMuPDF"""
    
    MAX_PDF_SIZE = 10 * 1024 * 1024  # 10MB limit
    MIN_TEXT_LENGTH = 50  # Minimum characters for valid resume
    
    @staticmethod
    async def extract_text_from_pdf(file: UploadFile) -> str:
        """
        Extract text from uploaded PDF file using PyMuPDF (3-5x faster than pdfplumber)
        
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
            
            # Check file size
            if len(content) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded PDF file is empty."
                )
            
            if len(content) > ResumeParser.MAX_PDF_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"PDF file too large. Maximum size is {ResumeParser.MAX_PDF_SIZE / (1024*1024)}MB."
                )
            
            # Extract text using PyMuPDF
            text = ""
            try:
                with fitz.open(stream=content, filetype="pdf") as pdf:
                    total_pages = len(pdf)
                    
                    if total_pages == 0:
                        raise HTTPException(
                            status_code=400,
                            detail="PDF contains no pages."
                        )
                    
                    
                    for page_num in range(total_pages):
                        page = pdf[page_num]
                        page_text = page.get_text()
                        if page_text:
                            text += page_text + "\n"
            
            except HTTPException:
                raise
            except Exception as pdf_error:
                error_msg = str(pdf_error).lower()
                
                if "password" in error_msg or "encrypted" in error_msg:
                    raise HTTPException(
                        status_code=400,
                        detail="PDF is password-protected or encrypted. Please upload an unprotected PDF."
                    )
                elif "corrupt" in error_msg or "invalid" in error_msg:
                    raise HTTPException(
                        status_code=400,
                        detail="PDF file appears to be corrupted or invalid. Please try a different file."
                    )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to read PDF: {str(pdf_error)}"
                    )
            
            # Check if any text was extracted
            if not text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract text from PDF. The file might be scanned or image-based. Please upload a text-based PDF or use OCR software to convert your resume first."
                )
            
            # Check minimum text length
            if len(text.strip()) < ResumeParser.MIN_TEXT_LENGTH:
                raise HTTPException(
                    status_code=400,
                    detail=f"Resume text is too short (found {len(text.strip())} characters, minimum {ResumeParser.MIN_TEXT_LENGTH} required). Please ensure the PDF contains a complete resume."
                )
            
            # Truncate to maximum length
            cleaned_text = text.strip()
            
            return cleaned_text
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error processing PDF: {str(e)}"
            )