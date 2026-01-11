# app/services/llm_service.py

import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


class LLMService:
    """
    LLM service using Google Gemini for all AI interactions.
    Handles resume parsing, JD analysis, and candidate assessment.
    """
    
    def __init__(self):
        """Initialize Gemini LLM service"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.model = genai.GenerativeModel(self.model_name)
    
    
    def _call_gemini(self, prompt: str, temperature: float) -> str:
        """
        Make API call to Gemini
        
        Args:
            prompt: Full prompt text
            temperature: Controls randomness (0.0 to 1.0)
            
        Returns:
            Raw response text from Gemini
        """
        try:
            generation_config = {
                "temperature": temperature,
                "response_mime_type": "application/json"
            }
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    
    def _clean_json_response(self, raw_response: str) -> str:
        """
        Clean up response text to extract valid JSON
        
        Args:
            raw_response: Raw text from LLM
            
        Returns:
            Cleaned JSON string
        """
        cleaned = raw_response.strip()
        
        # Remove markdown code blocks
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        return cleaned.strip()
    
    
    def generate_json(self, prompt: str, temperature: float = 0.5) -> Dict[str, Any]:
        """
        Generate and parse JSON response from Gemini
        
        Args:
            prompt: Complete prompt with instructions
            temperature: Randomness control
            
        Returns:
            Parsed JSON as dictionary
            
        Raises:
            Exception: If API call fails or JSON is invalid
        """
        try:
            # Get response from Gemini
            raw_output = self._call_gemini(prompt, temperature)
            
            # Clean and parse
            cleaned_json = self._clean_json_response(raw_output)
            parsed_data = json.loads(cleaned_json)
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            raise Exception(
                f"Failed to parse JSON from Gemini. Error: {str(e)}\n"
                f"Response preview: {raw_output[:300]}"
            )
        except Exception as e:
            raise Exception(f"LLM generation failed: {str(e)}")
    
    
    def parse_resume(self, resume_text: str, prompt_template: str) -> Dict[str, Any]:
        """
        Extract structured information from resume
        
        Args:
            resume_text: Text extracted from PDF
            prompt_template: Prompt with {resume_text} placeholder
            
        Returns:
            Dict containing name, total_experience_years, skills, education, projects
        """
        prompt = prompt_template.format(resume_text=resume_text)
        return self.generate_json(prompt, temperature=0.2)
    
    
    def parse_job_description(self, jd_text: str, prompt_template: str) -> Dict[str, Any]:
        """
        Extract requirements from job description
        
        Args:
            jd_text: Job description text
            prompt_template: Prompt with {job_description} placeholder
            
        Returns:
            Dict containing required_skills, min_experience, nice_to_have_skills
        """
        prompt = prompt_template.format(job_description=jd_text)
        return self.generate_json(prompt, temperature=0.2)
    
    
    def create_final_analysis(
        self,
        candidate_name: str,
        total_experience: int,
        education: list,
        projects: list,
        resume_skills: list,
        job_required_skills: list,
        job_nice_to_have_skills: list,
        min_experience: int,
        matched_skills: list,
        missing_skills: list,
        matched_nice_to_have: list,
        match_percentage: float,
        prompt_template: str
    ) -> Dict[str, Any]:
        """
        Generate final candidate analysis based on matching results
        
        Args:
            candidate_name: Candidate's name
            total_experience: Years of experience
            education: List of education entries
            projects: List of projects
            resume_skills: All skills from resume
            job_required_skills: Required skills from JD
            job_nice_to_have_skills: Nice-to-have skills from JD
            min_experience: Minimum experience required
            matched_skills: Skills that matched
            missing_skills: Required skills not found
            matched_nice_to_have: Bonus skills found
            match_percentage: Calculated match percentage
            prompt_template: Prompt with all placeholders
            
        Returns:
            Dict containing candidate_summary, overall_fit, strengths, gaps, improvement_suggestions
        """
        prompt = prompt_template.format(
            candidate_name=candidate_name,
            total_experience=total_experience,
            education=education,
            projects=projects,
            resume_skills=resume_skills,
            job_required_skills=job_required_skills,
            job_nice_to_have_skills=job_nice_to_have_skills,
            min_experience=min_experience,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            matched_nice_to_have=matched_nice_to_have,
            match_percentage=match_percentage
        )
        
        return self.generate_json(prompt, temperature=0.4)


def get_llm_service() -> LLMService:
    """
    Factory function to get LLM service instance
    
    Returns:
        Configured LLMService instance
    """
    return LLMService()


# ============================================================================
# TESTING CODE
# ============================================================================

if __name__ == "__main__":
    import sys
    import os
    from datetime import datetime
    sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
    
    from app.utils.prompt_templates import (
        RESUME_EXTRACTION_PROMPT,
        JD_ANALYSIS_PROMPT,
        FINAL_ANALYSIS_PROMPT
    )
    
    try:
        # Setup paths
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        resume_path = os.path.abspath(os.path.join(base_dir, 'dummy_data', 'resume.txt'))
        jd_path = os.path.abspath(os.path.join(base_dir, 'dummy_data', 'jd.txt'))
        output_dir = os.path.abspath(os.path.join(base_dir, 'dummy_data', 'output'))
        
        print(f"Base directory: {base_dir}")
        print(f"Looking for resume at: {resume_path}")
        print(f"Looking for JD at: {jd_path}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Load test data
        with open(resume_path, 'r', encoding='utf-8') as f:
            RESUME_TEXT = f.read()
        
        with open(jd_path, 'r', encoding='utf-8') as f:
            JD_TEXT = f.read()
        
        print("Testing LLM Service...")
        
        # Initialize LLM service
        llm = get_llm_service()
        
        # Parse Resume
        resume_data = llm.parse_resume(RESUME_TEXT, RESUME_EXTRACTION_PROMPT)
        
        # Parse JD
        jd_data = llm.parse_job_description(JD_TEXT, JD_ANALYSIS_PROMPT)
        
        # Skill matching
        matched_required = list(set(resume_data.get("skills", [])) & set(jd_data.get("required_skills", [])))
        missing_required = list(set(jd_data.get("required_skills", [])) - set(resume_data.get("skills", [])))
        matched_nice = list(set(resume_data.get("skills", [])) & set(jd_data.get("nice_to_have_skills", [])))
        
        total_required = len(jd_data.get("required_skills", []))
        match_percentage = round((len(matched_required) / total_required * 100), 2) if total_required > 0 else 0
        
        # Generate final analysis
        analysis = llm.create_final_analysis(
            candidate_name=resume_data.get("name", "Unknown"),
            total_experience=resume_data.get("total_experience_years", 0),
            education=resume_data.get("education", []),
            projects=resume_data.get("projects", []),
            resume_skills=resume_data.get("skills", []),
            job_required_skills=jd_data.get("required_skills", []),
            job_nice_to_have_skills=jd_data.get("nice_to_have_skills", []),
            min_experience=jd_data.get("min_experience", 0),
            matched_skills=matched_required,
            missing_skills=missing_required,
            matched_nice_to_have=matched_nice,
            match_percentage=match_percentage,
            prompt_template=FINAL_ANALYSIS_PROMPT
        )
        
        # Write outputs to files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Resume extraction output
        with open(os.path.join(output_dir, f'resume_extracted_{timestamp}.json'), 'w', encoding='utf-8') as f:
            json.dump(resume_data, f, indent=2, ensure_ascii=False)
        
        # JD analysis output
        with open(os.path.join(output_dir, f'jd_analyzed_{timestamp}.json'), 'w', encoding='utf-8') as f:
            json.dump(jd_data, f, indent=2, ensure_ascii=False)
        
        # Final analysis output
        with open(os.path.join(output_dir, f'final_analysis_{timestamp}.json'), 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        # Summary report
        summary = {
            "test_timestamp": timestamp,
            "candidate_name": resume_data.get('name', 'N/A'),
            "experience_years": resume_data.get('total_experience_years', 0),
            "required_experience": jd_data.get('min_experience', 0),
            "match_percentage": match_percentage,
            "matched_skills_count": len(matched_required),
            "total_required_skills": total_required,
            "missing_skills_count": len(missing_required),
            "bonus_skills_count": len(matched_nice),
            "matched_skills": matched_required,
            "missing_skills": missing_required,
            "bonus_skills": matched_nice,
            "status": "SUCCESS"
        }
        
        with open(os.path.join(output_dir, f'test_summary_{timestamp}.json'), 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Test completed successfully!")
        print(f"✓ Results saved to: dummy_data/output/")
        print(f"  - resume_extracted_{timestamp}.json")
        print(f"  - jd_analyzed_{timestamp}.json")
        print(f"  - final_analysis_{timestamp}.json")
        print(f"  - test_summary_{timestamp}.json")
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        print(traceback.format_exc())