"""Skill extraction from job descriptions and resumes."""

import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SkillExtractor:
    """
    Extract skills from text using pattern matching and NLP.

    Supports both predefined skill taxonomy and dynamic extraction.
    """

    # Common programming languages and frameworks
    TECH_SKILLS = [
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php', 'go', 'rust', 'swift', 'kotlin',
        'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'express',
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git',
        'machine learning', 'deep learning', 'nlp', 'computer vision', 'data science',
        'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy'
    ]

    # Soft skills
    SOFT_SKILLS = [
        'communication', 'leadership', 'teamwork', 'problem solving', 'analytical thinking',
        'project management', 'time management', 'adaptability', 'creativity', 'critical thinking',
        'collaboration', 'decision making', 'organization', 'presentation', 'negotiation'
    ]

    # Business/domain skills
    BUSINESS_SKILLS = [
        'agile', 'scrum', 'kanban', 'business analysis', 'requirements gathering',
        'stakeholder management', 'strategic planning', 'budgeting', 'forecasting',
        'market research', 'competitive analysis', 'product management', 'ux design', 'ui design'
    ]

    def __init__(self, skill_taxonomy: Optional[list[str]] = None):
        """
        Initialize skill extractor.

        Args:
            skill_taxonomy: Optional custom skill taxonomy
        """
        if skill_taxonomy:
            self.skill_taxonomy = [s.lower() for s in skill_taxonomy]
        else:
            # Combine all predefined skill lists
            self.skill_taxonomy = [
                s.lower() for s in
                self.TECH_SKILLS + self.SOFT_SKILLS + self.BUSINESS_SKILLS
            ]

    def extract_from_text(self, text: str) -> list[str]:
        """
        Extract skills from text using pattern matching.

        Args:
            text: Input text (job description, resume, etc.)

        Returns:
            List of extracted skills
        """
        if not text:
            return []

        text_lower = text.lower()
        found_skills = set()

        # Match skills from taxonomy
        for skill in self.skill_taxonomy:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)

        # Extract additional skills using common patterns
        # Pattern: "X years of experience in Y"
        experience_pattern = r'(?:experience (?:in|with)|proficient in|skilled in|knowledge of)\s+([\w\s,]+?)(?:\.|,|\n|and)'
        matches = re.finditer(experience_pattern, text_lower, re.IGNORECASE)

        for match in matches:
            skills_text = match.group(1)
            # Split by commas and 'and'
            potential_skills = re.split(r',|\sand\s', skills_text)
            for skill in potential_skills:
                skill = skill.strip()
                if len(skill) > 2 and len(skill) < 50:  # Reasonable skill name length
                    found_skills.add(skill)

        return sorted(list(found_skills))

    def extract_from_job(self, job) -> list[str]:
        """
        Extract skills from a Job model object.

        Args:
            job: Job model instance

        Returns:
            List of extracted skills
        """
        # Combine title, description, and requirements
        text = f"{job.title} {job.description} {job.requirements or ''}"
        return self.extract_from_text(text)

    def extract_from_resume(self, resume_text: str) -> list[str]:
        """
        Extract skills from resume text.

        Args:
            resume_text: Full resume text

        Returns:
            List of extracted skills
        """
        return self.extract_from_text(resume_text)

    def match_to_taxonomy(self, extracted: list[str]) -> list[str]:
        """
        Normalize extracted skills to standard taxonomy.

        Args:
            extracted: List of extracted skill strings

        Returns:
            List of normalized skills matching taxonomy
        """
        normalized = set()

        for skill in extracted:
            skill_lower = skill.lower().strip()

            # Direct match
            if skill_lower in self.skill_taxonomy:
                normalized.add(skill_lower)
            else:
                # Fuzzy matching - check if any taxonomy skill is contained
                for tax_skill in self.skill_taxonomy:
                    if tax_skill in skill_lower or skill_lower in tax_skill:
                        normalized.add(tax_skill)
                        break

        return sorted(list(normalized))

    def extract_and_normalize(self, text: str) -> list[str]:
        """
        Extract skills and normalize to taxonomy in one step.

        Args:
            text: Input text

        Returns:
            List of normalized skills
        """
        extracted = self.extract_from_text(text)
        normalized = self.match_to_taxonomy(extracted)
        return normalized

    def categorize_skills(self, skills: list[str]) -> dict[str, list[str]]:
        """
        Categorize skills into technical, soft, and business categories.

        Args:
            skills: List of skills

        Returns:
            Dictionary with categorized skills
        """
        categories = {
            'technical': [],
            'soft': [],
            'business': [],
            'other': []
        }

        skills_lower = [s.lower() for s in skills]

        for skill in skills_lower:
            if any(tech.lower() == skill for tech in self.TECH_SKILLS):
                categories['technical'].append(skill)
            elif any(soft.lower() == skill for soft in self.SOFT_SKILLS):
                categories['soft'].append(skill)
            elif any(biz.lower() == skill for biz in self.BUSINESS_SKILLS):
                categories['business'].append(skill)
            else:
                categories['other'].append(skill)

        return categories
