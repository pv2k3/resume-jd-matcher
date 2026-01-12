# app/utils/prompt_templates.py

RESUME_EXTRACTION_PROMPT = """
Extract key information from this resume and return ONLY valid JSON with this exact structure:

{{
  "name": "candidate full name",
  "total_experience_years": 0,
  "skills": ["skill1", "skill2"],
  "education": ["degree - institution"],
  "projects": ["project title - brief description"]
}}

Rules:
- Return ONLY the JSON object, no other text
- total_experience_years must be a number (integer or float)
- All arrays must contain strings
- Use empty arrays [] if no data found
- Use empty string "" for name if not found
- Use 0 for experience if not found

Resume to analyze:
{resume_text}
"""


JD_ANALYSIS_PROMPT = """
Extract requirements from this job description and return ONLY valid JSON with this exact structure:

{{
  "required_skills": ["skill1", "skill2"],
  "min_experience": 0,
  "nice_to_have_skills": ["skill1", "skill2"]
}}

Rules:
- Return ONLY the JSON object, no other text
- min_experience must be a number (integer or float)
- All arrays must contain strings
- Use empty arrays [] if no skills mentioned
- Use 0 for experience if not specified

Job description to analyze:
{job_description}
"""


FINAL_ANALYSIS_PROMPT = """
Generate a candidate assessment and return ONLY valid JSON with this exact structure:

{{
  "candidate_summary": "brief professional summary",
  "strengths": ["strength 1", "strength 2"],
  "gaps": ["gap 1", "gap 2"],
  "improvement_suggestions": ["suggestion 1", "suggestion 2"]
}}

Rules:
- Return ONLY the JSON object, no other text
- All fields are required
- All arrays must contain at least 1-2 items
- Keep items concise but meaningful (1-2 sentences each)
- Focus on actionable insights
- candidate_summary should be 2-3 sentences max

Input data for analysis:
- Candidate: {candidate_name}
- Experience: {total_experience} years (Job requires: {min_experience} years)
- Education: {education}
- Projects: {projects}
- Candidate Skills: {resume_skills}
- Required Skills: {job_required_skills}
- Nice-to-Have Skills: {job_nice_to_have_skills}
- Matched Required Skills: {matched_skills}
- Missing Required Skills: {missing_skills}
- Matched Nice-to-Have Skills: {matched_nice_to_have}
- Match Percentage: {match_percentage}%

Analysis Guidelines:
- Strengths: Highlight matched skills, relevant experience, strong qualifications
- Gaps: Focus on missing required skills, experience shortfalls, specific weaknesses
- Improvements: Provide specific, actionable steps to close gaps (courses, projects, certifications)

Generate the assessment now.
"""