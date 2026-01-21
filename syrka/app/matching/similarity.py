"""Similarity scoring for job-candidate matching."""

import numpy as np
from typing import Optional
import logging

from app.rag.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class SimilarityScorer:
    """
    Calculate various similarity scores between users and jobs.

    Supports cosine similarity, skill overlap, and semantic similarity.
    """

    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        """
        Initialize similarity scorer.

        Args:
            embedding_service: Optional embedding service for semantic similarity
        """
        self.embedding_service = embedding_service

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0 to 1)
        """
        if vec1 is None or vec2 is None:
            return 0.0

        # Normalize vectors
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
        vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)

        # Compute cosine similarity
        similarity = np.dot(vec1_norm, vec2_norm)

        # Ensure result is between 0 and 1
        return float(max(0.0, min(1.0, similarity)))

    def batch_similarity(self, query: np.ndarray, candidates: np.ndarray) -> np.ndarray:
        """
        Calculate cosine similarity between query and multiple candidate vectors.

        Args:
            query: Query vector (1D)
            candidates: Candidate vectors (2D array, each row is a vector)

        Returns:
            Array of similarity scores
        """
        if query is None or candidates is None or len(candidates) == 0:
            return np.array([])

        # Reshape query if needed
        if query.ndim == 1:
            query = query.reshape(1, -1)

        # Normalize query
        query_norm = query / (np.linalg.norm(query) + 1e-8)

        # Normalize candidates
        candidates_norm = candidates / (np.linalg.norm(candidates, axis=1, keepdims=True) + 1e-8)

        # Compute similarities
        similarities = np.dot(query_norm, candidates_norm.T).flatten()

        # Ensure all values are between 0 and 1
        similarities = np.clip(similarities, 0.0, 1.0)

        return similarities

    def skill_overlap_score(self, user_skills: list[str], job_skills: list[str]) -> float:
        """
        Calculate skill overlap score using Jaccard similarity.

        Args:
            user_skills: List of user's skills
            job_skills: List of job's required skills

        Returns:
            Jaccard similarity score (0 to 1)
        """
        if not user_skills or not job_skills:
            return 0.0

        # Normalize to lowercase for comparison
        user_set = set(s.lower().strip() for s in user_skills)
        job_set = set(s.lower().strip() for s in job_skills)

        # Calculate Jaccard similarity
        intersection = len(user_set & job_set)
        union = len(user_set | job_set)

        if union == 0:
            return 0.0

        score = intersection / union

        return float(score)

    def skill_coverage_score(self, user_skills: list[str], job_skills: list[str]) -> float:
        """
        Calculate what percentage of job requirements the user meets.

        Args:
            user_skills: List of user's skills
            job_skills: List of job's required skills

        Returns:
            Coverage score (0 to 1)
        """
        if not job_skills:
            return 1.0  # No requirements = full match

        if not user_skills:
            return 0.0

        # Normalize to lowercase
        user_set = set(s.lower().strip() for s in user_skills)
        job_set = set(s.lower().strip() for s in job_skills)

        # Calculate coverage
        matched = len(user_set & job_set)
        total_required = len(job_set)

        score = matched / total_required

        return float(score)

    def semantic_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Calculate semantic similarity between two texts using embeddings.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Semantic similarity score (0 to 1)
        """
        if not self.embedding_service:
            logger.warning("Embedding service not available for semantic similarity")
            return 0.0

        if not text1 or not text2:
            return 0.0

        # Generate embeddings
        vec1 = self.embedding_service.embed_text(text1)
        vec2 = self.embedding_service.embed_text(text2)

        # Calculate cosine similarity
        return self.cosine_similarity(vec1, vec2)

    def weighted_skill_score(
        self,
        user_skills: list[str],
        job_skills: list[str],
        skill_weights: Optional[dict[str, float]] = None
    ) -> float:
        """
        Calculate weighted skill match score.

        Args:
            user_skills: List of user's skills
            job_skills: List of job's required skills
            skill_weights: Optional dict mapping skills to importance weights

        Returns:
            Weighted skill score (0 to 1)
        """
        if not job_skills:
            return 1.0

        if not user_skills:
            return 0.0

        # Normalize skills
        user_set = set(s.lower().strip() for s in user_skills)
        job_set = set(s.lower().strip() for s in job_skills)

        if skill_weights is None:
            # Equal weights
            matched = len(user_set & job_set)
            return matched / len(job_set)

        # Calculate weighted score
        total_weight = 0.0
        matched_weight = 0.0

        for skill in job_set:
            weight = skill_weights.get(skill, 1.0)
            total_weight += weight

            if skill in user_set:
                matched_weight += weight

        if total_weight == 0:
            return 0.0

        return matched_weight / total_weight

    def get_matched_skills(
        self,
        user_skills: list[str],
        job_skills: list[str]
    ) -> tuple[list[str], list[str]]:
        """
        Get matched and missing skills.

        Args:
            user_skills: List of user's skills
            job_skills: List of job's required skills

        Returns:
            Tuple of (matched_skills, missing_skills)
        """
        # Normalize to lowercase
        user_set = set(s.lower().strip() for s in user_skills)
        job_set = set(s.lower().strip() for s in job_skills)

        matched = sorted(list(user_set & job_set))
        missing = sorted(list(job_set - user_set))

        return (matched, missing)
