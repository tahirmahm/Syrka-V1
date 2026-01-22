"""AI-powered CV generation and tailoring."""

import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings

logger = logging.getLogger(__name__)


class CVGenerator:
    """Generate and tailor CVs for specific job applications."""

    def __init__(self, llm_client=None):
        """
        Initialize CV generator.

        Args:
            llm_client: Optional LangChain LLM client
        """
        self.llm = llm_client or ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7
        )

        self.system_prompt = """You are an expert CV writer and career coach.
Your task is to tailor CVs to specific job requirements, highlighting relevant skills and experience.
Create professional, ATS-friendly CVs that maximize the candidate's chances."""

    def tailor_cv(self, user, job) -> str:
        """
        Generate tailored CV for a specific job.

        Args:
            user: User model instance
            job: Job model instance

        Returns:
            Tailored CV text
        """
        user_info = f"""
Name: {user.full_name}
Skills: {', '.join(user.skills)}
Experience: {user.experience_years} years
Location: {user.location or 'Not specified'}
Sector: {user.sector_preference or 'Open'}
Resume: {user.resume_text or 'No resume provided'}
"""

        job_info = f"""
Position: {job.title}
Company: {job.company}
Required Skills: {', '.join(job.skills_extracted)}
Description: {job.description[:500]}...
"""

        prompt = f"""Create a tailored CV for the following candidate applying to this job.

CANDIDATE INFORMATION:
{user_info}

JOB DETAILS:
{job_info}

Generate a professional CV that:
1. Highlights skills matching the job requirements
2. Emphasizes relevant experience
3. Uses keywords from the job description
4. Is ATS-friendly
5. Is concise (1-2 pages)

Format as plain text."""

        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]

            response = self.llm(messages)
            return response.content

        except Exception as e:
            logger.error(f"CV generation failed: {str(e)}")
            return f"CV for {user.full_name}\n\nSkills: {', '.join(user.skills)}\n\nExperience: {user.experience_years} years"

    def generate_sections(self, user, job) -> dict:
        """
        Generate structured CV sections.

        Args:
            user: User model instance
            job: Job model instance

        Returns:
            Dictionary of CV sections
        """
        sections = {
            'header': f"{user.full_name}\n{user.email}\n{user.location or ''}",
            'summary': self._generate_summary(user, job),
            'skills': ', '.join(user.skills),
            'experience': user.resume_text or '',
        }

        return sections

    def _generate_summary(self, user, job) -> str:
        """Generate professional summary."""
        prompt = f"""Write a 2-3 sentence professional summary for {user.full_name} applying for {job.title} at {job.company}.
Skills: {', '.join(user.skills[:5])}
Experience: {user.experience_years} years"""

        try:
            response = self.llm([HumanMessage(content=prompt)])
            return response.content
        except:
            return f"Experienced professional with {user.experience_years} years in {user.sector_preference or 'the industry'}."

    def format_as_text(self, sections: dict) -> str:
        """Format sections as plain text CV."""
        cv_text = f"""{sections['header']}

PROFESSIONAL SUMMARY
{sections['summary']}

SKILLS
{sections['skills']}

EXPERIENCE
{sections['experience']}
"""
        return cv_text
