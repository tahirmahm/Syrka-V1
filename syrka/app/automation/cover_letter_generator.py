"""AI-powered cover letter generation."""

import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings

logger = logging.getLogger(__name__)


class CoverLetterGenerator:
    """Generate personalized cover letters for job applications."""

    def __init__(self, llm_client=None, rag_chain=None):
        """
        Initialize cover letter generator.

        Args:
            llm_client: Optional LangChain LLM client
            rag_chain: Optional RAG chain for policy alignment
        """
        self.llm = llm_client or ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            temperature=0.7
        )
        self.rag_chain = rag_chain

        self.system_prompt = """You are an expert cover letter writer.
Create compelling, personalized cover letters that showcase the candidate's fit for the role.
Be professional, concise, and authentic."""

    def generate(
        self,
        user,
        job,
        include_policy_alignment: bool = False
    ) -> str:
        """
        Generate cover letter for job application.

        Args:
            user: User model instance
            job: Job model instance
            include_policy_alignment: Whether to mention national priorities

        Returns:
            Cover letter text
        """
        user_context = f"""
Name: {user.full_name}
Skills: {', '.join(user.skills[:8])}
Experience: {user.experience_years} years
Sector: {user.sector_preference or 'Various'}
"""

        job_context = f"""
Position: {job.title}
Company: {job.company}
Location: {job.location}
Key Requirements: {', '.join(job.skills_extracted[:5])}
"""

        prompt = f"""Write a professional cover letter for:

CANDIDATE:
{user_context}

JOB:
{job_context}

The cover letter should:
1. Express genuine interest in the role
2. Highlight 2-3 relevant skills/experiences
3. Show understanding of the company/role
4. Be concise (3-4 paragraphs)
5. Include a strong closing

Format as a formal business letter."""

        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]

            response = self.llm(messages)
            return response.content

        except Exception as e:
            logger.error(f"Cover letter generation failed: {str(e)}")
            return self._generate_fallback(user, job)

    def generate_with_context(
        self,
        user,
        job,
        additional_context: str
    ) -> str:
        """
        Generate cover letter with additional context.

        Args:
            user: User model instance
            job: Job model instance
            additional_context: Additional context to include

        Returns:
            Cover letter text
        """
        base_letter = self.generate(user, job)

        # Enhance with additional context
        prompt = f"""Enhance this cover letter by incorporating the following context:

{additional_context}

Original cover letter:
{base_letter}

Rewrite to naturally incorporate the context while maintaining professionalism."""

        try:
            response = self.llm([HumanMessage(content=prompt)])
            return response.content
        except:
            return base_letter

    def _generate_fallback(self, user, job) -> str:
        """Generate simple fallback cover letter."""
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job.title} position at {job.company}.

With {user.experience_years} years of experience and expertise in {', '.join(user.skills[:3])}, I am confident I would be a valuable addition to your team.

I am particularly drawn to this role because it aligns with my professional background and career goals.

Thank you for considering my application. I look forward to discussing how I can contribute to {job.company}.

Sincerely,
{user.full_name}
"""
