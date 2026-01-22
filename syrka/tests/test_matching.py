"""Job matching engine tests."""

import pytest
import numpy as np

from app.matching.skill_extractor import SkillExtractor
from app.matching.similarity import SimilarityScorer
from app.matching.heuristics import HeuristicScorer
from app.matching.ranker import JobRanker


@pytest.mark.unit
class TestSkillExtractor:
    """Test skill extraction from text."""

    def test_extract_tech_skills(self):
        """Test extracting technical skills."""
        extractor = SkillExtractor()
        text = "Looking for Python developer with FastAPI and Docker experience"
        skills = extractor.extract_from_text(text)
        assert "python" in skills
        assert "fastapi" in skills
        assert "docker" in skills

    def test_categorize_skills(self):
        """Test skill categorization."""
        extractor = SkillExtractor()
        skills = ["Python", "communication", "project management"]
        categories = extractor.categorize_skills(skills)
        assert "python" in categories["technical"]
        assert "communication" in categories["soft"]


@pytest.mark.unit
class TestHeuristicScorer:
    """Test heuristic scoring."""

    def test_location_score_exact_match(self):
        """Test location scoring with exact match."""
        scorer = HeuristicScorer()
        score = scorer.location_score("New York", "New York")
        assert score == 1.0

    def test_seniority_score(self):
        """Test seniority scoring."""
        scorer = HeuristicScorer()
        score = scorer.seniority_score(experience_years=6, job_seniority="senior")
        assert score >= 0.9
