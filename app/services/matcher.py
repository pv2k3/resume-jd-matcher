from typing import List, Dict


class SkillMatcher:
    """Python-based skill matching logic (not LLM-driven)"""
    
    @staticmethod
    def normalize_skill(skill: str) -> str:
        """
        Normalize skill name for comparison
        
        Args:
            skill: Raw skill name
            
        Returns:
            str: Normalized skill name
        """
        # Convert to lowercase and strip whitespace
        normalized = skill.lower().strip()
        
        # Remove common variations
        replacements = {
            'javascript': 'js',
            'typescript': 'ts',
            'node.js': 'nodejs',
            'react.js': 'react',
            'vue.js': 'vue',
            'angular.js': 'angular',
            'c++': 'cpp',
            'c#': 'csharp',
            'postgresql': 'postgres',
            'mongodb': 'mongo',
        }
        
        for original, replacement in replacements.items():
            if normalized == original:
                normalized = replacement
        
        return normalized
    
    @staticmethod
    def skills_match(skill1: str, skill2: str) -> bool:
        """
        Check if two skills match (fuzzy matching)
        
        Args:
            skill1: First skill
            skill2: Second skill
            
        Returns:
            bool: True if skills match
        """
        norm1 = SkillMatcher.normalize_skill(skill1)
        norm2 = SkillMatcher.normalize_skill(skill2)
        
        # Direct match
        if norm1 == norm2:
            return True
        
        # Substring match (e.g., "python" matches "python 3")
        if norm1 in norm2 or norm2 in norm1:
            return True
        
        return False
    
    @staticmethod
    def find_matched_skills(
        resume_skills: List[str],
        required_skills: List[str]
    ) -> tuple[List[str], List[str]]:
        """
        Find matched and missing skills
        
        Args:
            resume_skills: Skills from resume
            required_skills: Required skills from JD
            
        Returns:
            Tuple of (matched_skills, missing_skills)
        """
        matched = []
        missing = []
        
        for req_skill in required_skills:
            found = False
            for resume_skill in resume_skills:
                if SkillMatcher.skills_match(req_skill, resume_skill):
                    matched.append(req_skill)
                    found = True
                    break
            
            if not found:
                missing.append(req_skill)
        
        return matched, missing
    
    @staticmethod
    def calculate_match_percentage(
        matched_count: int,
        total_required: int
    ) -> float:
        """
        Calculate match percentage
        
        Args:
            matched_count: Number of matched skills
            total_required: Total required skills
            
        Returns:
            float: Match percentage (0-100)
        """
        if total_required == 0:
            return 100.0
        
        percentage = (matched_count / total_required) * 100
        return round(percentage, 2)
    
    @staticmethod
    def match_resume_to_jd(
        resume_skills: List[str],
        required_skills: List[str],
        nice_to_have_skills: List[str]
    ) -> Dict:
        """
        Main matching function
        
        Args:
            resume_skills: Skills from resume
            required_skills: Required skills from JD
            nice_to_have_skills: Nice-to-have skills from JD
            
        Returns:
            Dict with matched_skills, missing_skills, matched_nice_to_have, match_percentage
        """
        # Find matched and missing required skills
        matched_skills, missing_skills = SkillMatcher.find_matched_skills(
            resume_skills,
            required_skills
        )
        
        # Find matched nice-to-have skills
        matched_nice_to_have, _ = SkillMatcher.find_matched_skills(
            resume_skills,
            nice_to_have_skills
        )
        
        # Calculate match percentage (based on required skills only)
        match_percentage = SkillMatcher.calculate_match_percentage(
            len(matched_skills),
            len(required_skills)
        )
        
        return {
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "matched_nice_to_have": matched_nice_to_have,
            "match_percentage": match_percentage
        }