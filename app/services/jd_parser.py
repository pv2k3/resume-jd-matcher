from fastapi import HTTPException


class JDParser:
    """Service to parse and validate job descriptions"""
    
    MIN_JD_LENGTH = 50  # Minimum characters for a valid JD
    
    @staticmethod
    def validate_and_clean(jd_text: str) -> str:
        """
        Validate and clean job description text
        
        Args:
            jd_text: Raw job description text
            
        Returns:
            str: Cleaned and validated job description
            
        Raises:
            HTTPException: If JD is invalid or too short
        """
        if not jd_text or not isinstance(jd_text, str):
            raise HTTPException(
                status_code=400,
                detail="Job description is required and must be text."
            )
        
        # Clean the text
        cleaned_text = jd_text.strip()
        
        # Validate minimum length
        if len(cleaned_text) < JDParser.MIN_JD_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Job description is too short. Minimum {JDParser.MIN_JD_LENGTH} characters required."
            )
        
        return cleaned_text
    
    @staticmethod
    def is_technical_jd(jd_text: str) -> bool:
        """
        Determine if JD is technical or non-technical
        (Currently just a helper method, can be expanded)
        
        Args:
            jd_text: Job description text
            
        Returns:
            bool: True if technical, False otherwise
        """
        technical_keywords = [
            'programming', 'software', 'developer', 'engineer', 'code',
            'python', 'java', 'javascript', 'database', 'api', 'backend',
            'frontend', 'cloud', 'aws', 'azure', 'devops'
        ]
        
        jd_lower = jd_text.lower()
        return any(keyword in jd_lower for keyword in technical_keywords)