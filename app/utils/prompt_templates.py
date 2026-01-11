# app/utils/prompt_templates.py

# Resume Analysis Prompt Templates

# Prompt 1: Extract Resume Information

RESUME_EXTRACTION_PROMPT = """
You're helping extract key information from resumes into a structured format.
Pull out the important details and return them as clean JSON - no extra text or formatting.

Here's what we need:
{{
  "name": "",
  "total_experience_years": 0,
  "skills": [],
  "education": [],
  "projects": []
}}

Guidelines:
- Experience should be in years (whole number)
- Keep skill names consistent (like "Python" not "python programming")
- For education, grab the degree and school name
- Projects need a title and quick description
- Leave fields empty if info isn't there
- Must be valid JSON that can be parsed

Example 1:
Resume: "Sarah Chen has been working as a data analyst for 5 years. She specializes in SQL, Tableau, and Python. She graduated with an MS in Data Science from Stanford University and holds a BS in Mathematics from UC Berkeley. Her notable work includes building a customer churn prediction model and creating an executive dashboard for sales analytics."

Output:
{{
  "name": "Sarah Chen",
  "total_experience_years": 5,
  "skills": ["SQL", "Tableau", "Python"],
  "education": ["MS Data Science - Stanford University", "BS Mathematics - UC Berkeley"],
  "projects": ["Customer churn prediction model - ML system to forecast customer retention", "Executive sales dashboard - Analytics visualization for leadership team"]
}}

Example 2:
Resume: "Mike Rodriguez, fullstack developer, 2 years experience. Works with React, Node.js, and MongoDB. BCA from Delhi University. Built an e-commerce platform and a real-time chat application."

Output:
{{
  "name": "Mike Rodriguez",
  "total_experience_years": 2,
  "skills": ["React", "Node.js", "MongoDB"],
  "education": ["BCA - Delhi University"],
  "projects": ["E-commerce platform - Online shopping web application", "Real-time chat app - Instant messaging system"]
}}

Now extract from this resume:
{resume_text}
"""


# Prompt 2: Analyze Job Requirements

JD_ANALYSIS_PROMPT = """
Break down this job posting and tell me what they're really looking for.
Return the info as clean JSON.

Structure needed:
{{
  "required_skills": [],
  "min_experience": 0,
  "nice_to_have_skills": []
}}

What to look for:
- Required skills are the must-haves they mention
- Nice-to-have are the bonus or preferred items
- Experience in years (use 0 if not specified)
- Return valid JSON only

Example 1:
Job Post: "Seeking a frontend engineer with at least 3 years building modern web apps. You must be proficient in React and TypeScript. Experience with Next.js and GraphQL is a plus. We value clean code and strong communication skills."

Output:
{{
  "required_skills": ["React", "TypeScript"],
  "min_experience": 3,
  "nice_to_have_skills": ["Next.js", "GraphQL"]
}}

Example 2:
Job Post: "DevOps role requiring Kubernetes and Terraform expertise. Should have worked with CI/CD pipelines. Familiarity with monitoring tools like Prometheus would be great. Looking for someone with around 4+ years in infrastructure."

Output:
{{
  "required_skills": ["Kubernetes", "Terraform", "CI/CD"],
  "min_experience": 4,
  "nice_to_have_skills": ["Prometheus"]
}}

Example 3:
Job Post: "Junior position for mobile developers. Need someone who knows Flutter. Firebase knowledge is beneficial but we can train the right person."

Output:
{{
  "required_skills": ["Flutter"],
  "min_experience": 0,
  "nice_to_have_skills": ["Firebase"]
}}

Analyze this job description:
{job_description}
"""


# Prompt 3: Generate Candidate Assessment

FINAL_ANALYSIS_PROMPT = """
You're doing a final assessment of how well a candidate fits a job opening based on the matching analysis already completed.

Look at the data provided and write a professional evaluation.

Return this structure as JSON:
{{
  "candidate_summary": "",
  "overall_fit": "",
  "strengths": [],
  "gaps": [],
  "improvement_suggestions": []
}}

What you're given:
- Candidate name and experience level
- Skills they have vs skills the job needs
- Which skills matched and which are missing
- The calculated match percentage
- Education background
- Project experience

Keep in mind:
- Strengths should highlight matched skills and relevant experience
- Gaps should focus on missing required skills and experience shortfalls
- Suggestions should be actionable and specific
- Overall fit should consider both skills match and experience level
- Must return valid JSON only

Example 1:
Input Data:
- Name: Sarah Chen
- Experience: 5 years
- Resume Skills: ["Python", "Django", "PostgreSQL", "AWS"]
- Job Required: ["Python", "Django", "Redis", "AWS"]
- Job Min Experience: 3 years
- Matched Skills: ["Python", "Django", "AWS"]
- Missing Skills: ["Redis"]
- Match Percentage: 75%
- Education: ["MS Data Science - Stanford"]
- Projects: ["API development", "Database optimization"]

Output:
{{
  "candidate_summary": "Experienced backend engineer with 5 years in the field, strong Python and Django expertise with cloud deployment experience",
  "overall_fit": "Strong match - meets experience requirement and has 75% skill alignment with minor gaps in caching technologies",
  "strengths": ["Solid Python and Django foundation covering core requirements", "Exceeds minimum experience by 2 years", "Cloud experience with AWS aligns with job needs", "Graduate degree in relevant field", "Hands-on API and database work shown in projects"],
  "gaps": ["Missing Redis experience which is required for the role", "No specific mention of caching implementation"],
  "improvement_suggestions": ["Learn Redis fundamentals through their official tutorial - should take a few days", "Build a small project implementing Redis caching with Django", "Review common caching patterns and strategies used in production systems"]
}}

Example 2:
Input Data:
- Name: Raj Kumar
- Experience: 1 year
- Resume Skills: ["JavaScript", "Vue.js", "HTML", "CSS"]
- Job Required: ["React", "TypeScript", "Node.js"]
- Job Min Experience: 3 years
- Matched Skills: ["JavaScript"]
- Missing Skills: ["React", "TypeScript", "Node.js"]
- Match Percentage: 25%
- Education: ["BCA - Mumbai University"]
- Projects: ["Personal blog", "Todo app"]

Output:
{{
  "candidate_summary": "Junior frontend developer with 1 year experience, currently working with Vue.js but missing several key technologies for this role",
  "overall_fit": "Not a strong match - significant gaps in required technologies and below experience threshold",
  "strengths": ["Good JavaScript fundamentals which translate across frameworks", "Web development foundation with HTML/CSS", "Framework experience with Vue.js shows modern dev understanding"],
  "gaps": ["Needs React experience instead of Vue.js", "TypeScript is required but not present", "Backend skills with Node.js are missing", "Only 1 year experience vs 3 year minimum"],
  "improvement_suggestions": ["Transition from Vue to React - many concepts overlap, start with React docs", "Pick up TypeScript alongside React for better learning", "Build a fullstack project using React + Node.js to cover multiple gaps", "Consider junior roles that match current experience level while building these skills"]
}}

Example 3:
Input Data:
- Name: Priya Singh
- Experience: 4 years
- Resume Skills: ["Java", "Spring Boot", "MySQL", "Docker", "Kubernetes"]
- Job Required: ["Java", "Spring Boot", "Microservices", "Docker"]
- Job Min Experience: 3 years
- Matched Skills: ["Java", "Spring Boot", "Docker"]
- Missing Skills: ["Microservices"]
- Nice to Have Match: ["Kubernetes"]
- Match Percentage: 75%
- Education: ["B.Tech Computer Science - IIT Delhi"]
- Projects: ["Payment gateway integration", "Container orchestration setup"]

Output:
{{
  "candidate_summary": "Mid-level backend developer with 4 years experience in Java ecosystem, strong containerization skills and top-tier education",
  "overall_fit": "Very good match - covers core technologies with 75% alignment and brings valuable bonus skills",
  "strengths": ["Strong Java and Spring Boot expertise matching core requirements", "Meets experience requirement comfortably", "Docker skills cover deployment needs", "Bonus Kubernetes knowledge adds significant value", "Relevant project work in payments and orchestration", "Strong educational background from premier institution"],
  "gaps": ["Microservices architecture not explicitly mentioned despite related skills"],
  "improvement_suggestions": ["Document any microservices work you've done - you likely have exposure given Spring Boot experience", "Review microservices design patterns and best practices", "If no direct experience, refactor a project to use microservices architecture"]
}}

Now generate the assessment for this candidate:

Candidate Information:
Name: {candidate_name}
Total Experience: {total_experience} years
Education: {education}
Projects: {projects}

Skills Analysis:
Candidate Skills: {resume_skills}
Job Required Skills: {job_required_skills}
Job Nice-to-Have Skills: {job_nice_to_have_skills}
Minimum Experience Required: {min_experience} years

Matching Results:
Matched Required Skills: {matched_skills}
Missing Required Skills: {missing_skills}
Matched Nice-to-Have Skills: {matched_nice_to_have}
Overall Match Percentage: {match_percentage}%
"""