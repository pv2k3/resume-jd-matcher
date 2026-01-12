from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.schemas.response import HealthResponse, FinalAnalysis
from app.services.resume_parser import ResumeParser
from app.services.jd_parser import JDParser
from app.services.llm_service import LLMService
from app.services.matcher import SkillMatcher
from app.utils.prompt_templates import (
    RESUME_EXTRACTION_PROMPT,
    JD_ANALYSIS_PROMPT,
    FINAL_ANALYSIS_PROMPT
)
import asyncio

router = APIRouter()

# Initialize services
resume_parser = ResumeParser()
jd_parser = JDParser()
llm_service = LLMService()
skill_matcher = SkillMatcher()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns:
        HealthResponse: Service health status
    """
    return HealthResponse(
        status="healthy",
        message="Resume Analyzer API is running"
    )


@router.post("/analyze", response_model=FinalAnalysis)
async def analyze_resume(
    resume: UploadFile = File(..., description="Resume PDF file"),
    job_description: str = Form(..., description="Job description text")
):
    """
    Analyze resume against job description
    
    Args:
        resume: PDF file of candidate's resume
        job_description: Text of the job description
        
    Returns:
        FinalAnalysis: Comprehensive analysis of candidate fit
    """
    try:
        # Step 1: Extract text from resume PDF
        resume_text = await resume_parser.extract_text_from_pdf(resume)
        
        # Step 2: Validate and clean job description
        jd_text = jd_parser.validate_and_clean(job_description)
        
        # Step 3 & 4: Run LLM extractions in parallel
        resume_data, jd_data = await asyncio.gather(
            asyncio.to_thread(lambda: llm_service.parse_resume(resume_text, RESUME_EXTRACTION_PROMPT)),
            asyncio.to_thread(lambda: llm_service.parse_job_description(jd_text, JD_ANALYSIS_PROMPT))
        )
        
        # Step 5: Match resume to JD
        matching_result = skill_matcher.match_resume_to_jd(
            resume_skills=resume_data.get("skills", []),
            required_skills=jd_data.get("required_skills", []),
            nice_to_have_skills=jd_data.get("nice_to_have_skills", [])
        )
        
        # Step 6: Generate final analysis
        analysis_data = llm_service.create_final_analysis(
            candidate_name=resume_data.get("name", "Unknown"),
            total_experience=resume_data.get("total_experience_years", 0),
            education=resume_data.get("education", []),
            projects=resume_data.get("projects", []),
            resume_skills=resume_data.get("skills", []),
            job_required_skills=jd_data.get("required_skills", []),
            job_nice_to_have_skills=jd_data.get("nice_to_have_skills", []),
            min_experience=jd_data.get("min_experience", 0),
            matched_skills=matching_result["matched_skills"],
            missing_skills=matching_result["missing_skills"],
            matched_nice_to_have=matching_result["matched_nice_to_have"],
            match_percentage=matching_result["match_percentage"],
            prompt_template=FINAL_ANALYSIS_PROMPT
        )
        
        # Step 7: Construct final response
        final_analysis = FinalAnalysis(
            candidate_summary=analysis_data["candidate_summary"],
            match_percentage=matching_result["match_percentage"],
            strengths=analysis_data["strengths"],
            gaps=analysis_data["gaps"],
            improvement_suggestions=analysis_data["improvement_suggestions"]
        )
        
        return final_analysis
        
    except HTTPException as he:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during analysis: {str(e)}"
        )