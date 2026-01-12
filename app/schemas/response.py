from pydantic import BaseModel, Field
from typing import List


class ResumeInfo(BaseModel):
    """Structured information extracted from resume"""
    name: str = Field(..., description="Candidate's full name")
    total_experience_years: float = Field(..., ge=0, description="Total years of experience")
    skills: List[str] = Field(..., description="List of skills")
    education: List[str] = Field(..., description="Educational qualifications")
    projects: List[str] = Field(..., description="Notable projects")


class JobDescriptionInfo(BaseModel):
    """Structured information extracted from job description"""
    required_skills: List[str] = Field(..., description="Required skills for the job")
    min_experience: float = Field(..., ge=0, description="Minimum years of experience required")
    nice_to_have_skills: List[str] = Field(default_factory=list, description="Optional/preferred skills")


class MatchingResult(BaseModel):
    """Result of resume-JD matching"""
    matched_skills: List[str] = Field(..., description="Skills that match between resume and JD")
    missing_skills: List[str] = Field(..., description="Required skills missing from resume")
    match_percentage: float = Field(..., ge=0, le=100, description="Overall match percentage")


class FinalAnalysis(BaseModel):
    """Final consolidated analysis output - POC Compliant"""
    candidate_summary: str = Field(..., description="Brief summary of the candidate")
    match_percentage: float = Field(..., ge=0, le=100, description="Overall match percentage")
    strengths: List[str] = Field(..., description="Candidate's strengths for this role")
    gaps: List[str] = Field(..., description="Areas where candidate falls short")
    improvement_suggestions: List[str] = Field(..., description="Suggestions for improvement")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str