"""Curriculum generation using LLM."""

import logging
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Optional

from app.curriculum.templates import *
from app.curriculum.structure import *
from app.config import settings

logger = logging.getLogger(__name__)


class CurriculumGenerator:
    """Generate complete curricula using AI."""

    def __init__(self, llm_client=None, rag_chain=None):
        """Initialize curriculum generator."""
        self.llm = llm_client or ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7
        )
        self.rag_chain = rag_chain

    def generate_curriculum(
        self,
        sector: str,
        skills: list[str],
        policy_context: bool = True
    ) -> FullCurriculum:
        """Generate complete curriculum."""
        logger.info(f"Generating curriculum for {sector} with {len(skills)} skills")

        modules = []

        # Group skills into modules (simplified)
        skill_groups = [skills[i:i+3] for i in range(0, len(skills), 3)]

        for idx, skill_group in enumerate(skill_groups[:6]):
            module = self.generate_module(
                topic=f"{sector} Module {idx+1}",
                skills=skill_group,
                duration_hours=40
            )
            modules.append(module)

        curriculum = FullCurriculum(
            title=f"{sector} Professional Development Program",
            modules=modules,
            target_sector=sector,
            target_skills=skills,
            policy_alignment=0.0
        )

        return curriculum

    def generate_module(
        self,
        topic: str,
        skills: list[str],
        duration_hours: int
    ) -> Module:
        """Generate a curriculum module."""
        units = []

        for skill in skills:
            unit = self.generate_unit(f"{skill} Fundamentals", [skill])
            units.append(unit)

        module = Module(
            title=topic,
            description=f"Comprehensive training on {', '.join(skills)}",
            units=units,
            total_duration=duration_hours
        )

        return module

    def generate_unit(
        self,
        module_context: str,
        competencies: list[str]
    ) -> Unit:
        """Generate a curriculum unit."""
        unit = Unit(
            title=module_context,
            competencies=[
                Competency(
                    name=comp,
                    description=f"Develop proficiency in {comp}",
                    proficiency_level="Intermediate"
                ) for comp in competencies
            ],
            outcomes=[
                LearningOutcome(
                    statement=f"Apply {comp} in practical scenarios",
                    bloom_level="Apply",
                    measurable_criteria=f"Successfully complete {comp} project"
                ) for comp in competencies
            ],
            assessments=[
                Assessment(
                    type="Project",
                    criteria=["Functionality", "Code quality", "Documentation"],
                    weight=1.0,
                    rubric=None
                )
            ],
            duration_hours=10
        )

        return unit

    def align_with_policy(
        self,
        curriculum: FullCurriculum,
        sector: str
    ) -> float:
        """Compute policy alignment score."""
        # Simplified - production would use RAG
        return 0.75

    def enhance_with_policy(
        self,
        curriculum: FullCurriculum
    ) -> FullCurriculum:
        """Enhance curriculum with policy priorities."""
        return curriculum
