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
import asyncio
import os
import hashlib
from datetime import datetime
from pathlib import Path
from functools import lru_cache

router = APIRouter()

# Initialize services
resume_parser = ResumeParser()
jd_parser = JDParser()
llm_service = LLMService()
skill_matcher = SkillMatcher()

# Performance settings
SAVE_DEBUG_FILES = os.getenv("SAVE_DEBUG_FILES", "false").lower() == "true"

# ⚡ CACHE: Store recently analyzed JDs (in-memory cache)
jd_cache = {}
MAX_CACHE_SIZE = 50

ROOT_DIR = Path(__file__).parent.parent.parent
TEST_OUTPUT_DIR = ROOT_DIR / "test_output"
if SAVE_DEBUG_FILES:
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)


def save_output(filename: str, data: dict, timestamp: str):
    """Save output data to JSON file in test_output folder"""
    filepath = TEST_OUTPUT_DIR / f"{timestamp}_{filename}"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_jd_hash(jd_text: str) -> str:
    """Generate hash for JD text for caching"""
    return hashlib.md5(jd_text.encode()).hexdigest()


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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        print(f"\n{'='*80}")
        print(f"🚀 Starting Analysis - Session: {timestamp}")
        print(f"{'='*80}\n")
        
        # Step 1: Extract text from resume PDF
        print("📄 Step 1: Extracting text from PDF...")
        resume_text = await resume_parser.extract_text_from_pdf(resume)
        print(f"   ✅ Resume text extracted ({len(resume_text)} chars)\n")
        
        # Step 2: Validate and clean job description
        print("📋 Step 2: Validating job description...")
        jd_text = jd_parser.validate_and_clean(job_description)
        jd_hash = get_jd_hash(jd_text)
        print(f"   ✅ JD validated ({len(jd_text)} chars)\n")
        
        # ⚡ OPTIMIZATION: Check if JD was recently analyzed (cache hit)
        jd_cached = jd_hash in jd_cache
        
        if jd_cached:
            print("🤖 Steps 3 & 4: Resume extraction + JD cache hit...")
            # Only parse resume, use cached JD
            resume_data = await asyncio.to_thread(
                lambda: llm_service.parse_resume(resume_text, RESUME_EXTRACTION_PROMPT)
            )
            jd_data = jd_cache[jd_hash]
            print("   ✅ Resume extracted, JD retrieved from cache 🚀\n")
        else:
            print("🤖 Steps 3 & 4: Running LLM extractions in parallel...")
            # Run both LLM calls concurrently
            resume_data, jd_data = await asyncio.gather(
                asyncio.to_thread(lambda: llm_service.parse_resume(resume_text, RESUME_EXTRACTION_PROMPT)),
                asyncio.to_thread(lambda: llm_service.parse_job_description(jd_text, JD_ANALYSIS_PROMPT))
            )
            
            # ⚡ Cache the JD result
            if len(jd_cache) >= MAX_CACHE_SIZE:
                # Remove oldest entry
                jd_cache.pop(next(iter(jd_cache)))
            jd_cache[jd_hash] = jd_data
            
            print("   ✅ Resume & JD data extracted in parallel\n")
        
        print(f"      Name: {resume_data.get('name', 'N/A')}")
        print(f"      Experience: {resume_data.get('total_experience_years', 0)} years")
        print(f"      Skills: {len(resume_data.get('skills', []))} found")
        print(f"      Required skills: {len(jd_data.get('required_skills', []))} found\n")
        
        # Step 5: Match resume to JD using Python logic (fast)
        print("🔍 Step 5: Matching skills...")
        matching_result = skill_matcher.match_resume_to_jd(
            resume_skills=resume_data.get("skills", []),
            required_skills=jd_data.get("required_skills", []),
            nice_to_have_skills=jd_data.get("nice_to_have_skills", [])
        )
        print(f"   ✅ Match: {matching_result['match_percentage']}%\n")
        
        # Step 6: Generate final analysis using LLM
        print("🤖 Step 6: Generating final analysis...")
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
        print(f"   ✅ Final analysis generated\n")
        
        # Step 7: Construct final response
        print("📦 Step 7: Creating final API response...")
        final_analysis = FinalAnalysis(
            candidate_summary=analysis_data["candidate_summary"],
            match_percentage=matching_result["match_percentage"],
            strengths=analysis_data["strengths"],
            gaps=analysis_data["gaps"],
            improvement_suggestions=analysis_data["improvement_suggestions"]
        )
        
        # ⚡ OPTIMIZATION: Save outputs asynchronously (only if debug enabled)
        if SAVE_DEBUG_FILES:
            asyncio.create_task(save_analysis_outputs(
                timestamp, resume, resume_text, jd_text,
                resume_data, jd_data, matching_result,
                analysis_data, final_analysis, jd_cached
            ))
        
        print(f"{'='*80}")
        print(f"✅ Analysis Complete - {timestamp}")
        print(f"{'='*80}\n")
        
        return final_analysis
        
    except HTTPException as he:
        print(f"\n❌ HTTP Exception: {he.detail}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during analysis: {str(e)}"
        )


async def save_analysis_outputs(
    timestamp, resume, resume_text, jd_text,
    resume_data, jd_data, matching_result,
    analysis_data, final_analysis, jd_cached
):
    """
    Save all analysis outputs asynchronously (non-blocking)
    """
    try:
        save_output(
            "0_complete_summary.json",
            {
                "session_id": timestamp,
                "jd_cache_hit": jd_cached,
                "resume_extraction": resume_data,
                "jd_extraction": jd_data,
                "matching": matching_result,
                "final_analysis": final_analysis.model_dump()
            },
            timestamp
        )
        
        print(f"💾 Summary saved to test_output/{timestamp}_0_complete_summary.json")
        
    except Exception as e:
        print(f"⚠️  Warning: Failed to save outputs: {str(e)}") 