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
import json
import os
from datetime import datetime
from pathlib import Path

router = APIRouter()

# Initialize services
resume_parser = ResumeParser()
jd_parser = JDParser()
llm_service = LLMService()
skill_matcher = SkillMatcher()

# Create test_output directory at root level
ROOT_DIR = Path(__file__).parent.parent.parent
TEST_OUTPUT_DIR = ROOT_DIR / "test_output"
TEST_OUTPUT_DIR.mkdir(exist_ok=True)


def save_output(filename: str, data: dict, timestamp: str):
    """Save output data to JSON file in test_output folder"""
    filepath = TEST_OUTPUT_DIR / f"{timestamp}_{filename}"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved: {filepath.name}")


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
    # Generate timestamp for this analysis session
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        print(f"\n{'='*80}")
        print(f"🚀 Starting Analysis - Session: {timestamp}")
        print(f"{'='*80}\n")
        
        # Step 1: Extract text from resume PDF
        print("📄 Step 1: Extracting text from PDF...")
        resume_text = await resume_parser.extract_text_from_pdf(resume)
        
        save_output(
            "1_resume_extracted_text.json",
            {
                "filename": resume.filename,
                "text_length": len(resume_text),
                "extracted_text": resume_text
            },
            timestamp
        )
        print(f"   ✅ Resume text extracted ({len(resume_text)} chars)\n")
        
        # Step 2: Validate and clean job description
        print("📋 Step 2: Validating job description...")
        jd_text = jd_parser.validate_and_clean(job_description)
        
        save_output(
            "2_jd_cleaned.json",
            {
                "original_length": len(job_description),
                "cleaned_length": len(jd_text),
                "cleaned_text": jd_text
            },
            timestamp
        )
        print(f"   ✅ JD validated ({len(jd_text)} chars)\n")
        
        # Step 3: Extract structured information from resume using LLM
        print("🤖 Step 3: Extracting resume data with LLM...")
        resume_data = llm_service.parse_resume(resume_text, RESUME_EXTRACTION_PROMPT)
        
        save_output(
            "3_llm_resume_extraction.json",
            {
                "output": resume_data,
                "name": resume_data.get("name", "N/A"),
                "experience_years": resume_data.get("total_experience_years", 0),
                "skills_count": len(resume_data.get("skills", [])),
                "education_count": len(resume_data.get("education", [])),
                "projects_count": len(resume_data.get("projects", []))
            },
            timestamp
        )
        print(f"   ✅ Resume data extracted")
        print(f"      Name: {resume_data.get('name', 'N/A')}")
        print(f"      Experience: {resume_data.get('total_experience_years', 0)} years")
        print(f"      Skills: {len(resume_data.get('skills', []))} found\n")
        
        # Step 4: Extract structured information from JD using LLM
        print("🤖 Step 4: Extracting JD requirements with LLM...")
        jd_data = llm_service.parse_job_description(jd_text, JD_ANALYSIS_PROMPT)
        
        save_output(
            "4_llm_jd_extraction.json",
            {
                "output": jd_data,
                "required_skills_count": len(jd_data.get("required_skills", [])),
                "nice_to_have_count": len(jd_data.get("nice_to_have_skills", [])),
                "min_experience": jd_data.get("min_experience", 0)
            },
            timestamp
        )
        print(f"   ✅ JD data extracted")
        print(f"      Required skills: {len(jd_data.get('required_skills', []))} found")
        print(f"      Nice-to-have: {len(jd_data.get('nice_to_have_skills', []))} found")
        print(f"      Min experience: {jd_data.get('min_experience', 0)} years\n")
        
        # Step 5: Match resume to JD using Python logic
        print("🔍 Step 5: Matching skills (Python logic)...")
        matching_result = skill_matcher.match_resume_to_jd(
            resume_skills=resume_data.get("skills", []),
            required_skills=jd_data.get("required_skills", []),
            nice_to_have_skills=jd_data.get("nice_to_have_skills", [])
        )
        
        save_output(
            "5_skill_matching_results.json",
            {
                "input": {
                    "resume_skills": resume_data.get("skills", []),
                    "required_skills": jd_data.get("required_skills", []),
                    "nice_to_have_skills": jd_data.get("nice_to_have_skills", [])
                },
                "output": matching_result,
                "summary": {
                    "match_percentage": matching_result["match_percentage"],
                    "matched_count": len(matching_result["matched_skills"]),
                    "missing_count": len(matching_result["missing_skills"]),
                    "bonus_count": len(matching_result["matched_nice_to_have"])
                }
            },
            timestamp
        )
        print(f"   ✅ Matching completed")
        print(f"      Match: {matching_result['match_percentage']}%")
        print(f"      Matched: {len(matching_result['matched_skills'])} skills")
        print(f"      Missing: {len(matching_result['missing_skills'])} skills\n")
        
        # Step 6: Generate final analysis using LLM
        print("🤖 Step 6: Generating final analysis with LLM...")
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
        
        save_output(
            "6_llm_final_analysis.json",
            {
                "output": analysis_data,
                "summary": {
                    "strengths_count": len(analysis_data.get("strengths", [])),
                    "gaps_count": len(analysis_data.get("gaps", [])),
                    "suggestions_count": len(analysis_data.get("improvement_suggestions", []))
                }
            },
            timestamp
        )
        print(f"   ✅ Final analysis generated")
        print(f"      Strengths: {len(analysis_data.get('strengths', []))} items")
        print(f"      Gaps: {len(analysis_data.get('gaps', []))} items")
        print(f"      Suggestions: {len(analysis_data.get('improvement_suggestions', []))} items\n")
        
        # Step 7: Construct final response
        print("📦 Step 7: Creating final API response...")
        final_analysis = FinalAnalysis(
            candidate_summary=analysis_data["candidate_summary"],
            match_percentage=matching_result["match_percentage"],
            strengths=analysis_data["strengths"],
            gaps=analysis_data["gaps"],
            improvement_suggestions=analysis_data["improvement_suggestions"]
        )
        
        save_output(
            "7_final_api_response.json",
            final_analysis.model_dump(),
            timestamp
        )
        
        # Save complete summary
        save_output(
            "0_complete_summary.json",
            {
                "session_id": timestamp,
                "input": {
                    "resume_filename": resume.filename,
                    "jd_preview": jd_text[:200] + "..."
                },
                "resume_extraction": {
                    "name": resume_data.get("name", "N/A"),
                    "experience": resume_data.get("total_experience_years", 0),
                    "skills": resume_data.get("skills", []),
                    "education": resume_data.get("education", []),
                    "projects": resume_data.get("projects", [])
                },
                "jd_extraction": {
                    "required_skills": jd_data.get("required_skills", []),
                    "min_experience": jd_data.get("min_experience", 0),
                    "nice_to_have_skills": jd_data.get("nice_to_have_skills", [])
                },
                "matching": matching_result,
                "final_analysis": final_analysis.model_dump()
            },
            timestamp
        )
        
        print(f"   ✅ Final response created\n")
        print(f"{'='*80}")
        print(f"✅ Analysis Complete - Check test_output/{timestamp}_*.json")
        print(f"{'='*80}\n")
        
        return final_analysis
        
    except HTTPException as he:
        print(f"\n❌ HTTP Exception: {he.detail}")
        save_output(
            "error_log.json",
            {
                "error_type": "HTTPException",
                "status_code": he.status_code,
                "detail": he.detail,
                "timestamp": timestamp
            },
            timestamp
        )
        raise
    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")
        print(f"   Error Type: {type(e).__name__}")
        import traceback
        save_output(
            "error_log.json",
            {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": timestamp
            },
            timestamp
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during analysis: {str(e)}"
        )