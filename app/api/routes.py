from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.schemas.response import HealthResponse, FinalAnalysis
from app.services.resume_parser import ResumeParser
from app.services.jd_parser import JDParser
from app.services.llm_service import LLMService
from app.services.matcher import SkillMatcher

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
        
        # Step 3: Extract structured information from resume using LLM
        resume_info = llm_service.extract_resume_info(resume_text)
        
        # Step 4: Extract structured information from JD using LLM
        jd_info = llm_service.extract_jd_info(jd_text)
        
        # Step 5: Match resume to JD using Python logic
        matching_result = skill_matcher.match_resume_to_jd(resume_info, jd_info)
        
        # Step 6: Generate final analysis using LLM
        analysis_data = llm_service.generate_analysis(
            resume_info=resume_info,
            jd_info=jd_info,
            match_percentage=matching_result.match_percentage,
            matched_skills=matching_result.matched_skills,
            missing_skills=matching_result.missing_skills
        )
        
        # Step 7: Construct final response
        final_analysis = FinalAnalysis(
            candidate_summary=analysis_data["candidate_summary"],
            match_percentage=matching_result.match_percentage,
            strengths=analysis_data["strengths"],
            gaps=analysis_data["gaps"],
            improvement_suggestions=analysis_data["improvement_suggestions"]
        )
        
        return final_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during analysis: {str(e)}"
        )