"""Job ranking system combining multiple scoring components."""

import logging
from typing import Optional
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class JobRanker:
    """
    Rank jobs by combining similarity, skill overlap, and heuristic scores.

    Uses weighted combination to produce final match probability.
    """

    def __init__(self, weights: Optional[dict[str, float]] = None):
        """
        Initialize job ranker with scoring weights.

        Args:
            weights: Optional custom weights for score components
                    Default uses config settings
        """
        if weights:
            self.weights = weights
        else:
            self.weights = {
                'similarity': settings.MATCH_SIMILARITY_WEIGHT,
                'skill_overlap': settings.MATCH_SKILL_OVERLAP_WEIGHT,
                'heuristics': settings.MATCH_HEURISTIC_WEIGHT
            }

        # Normalize weights to sum to 1
        total_weight = sum(self.weights.values())
        self.weights = {k: v / total_weight for k, v in self.weights.items()}

        logger.info(f"JobRanker initialized with weights: {self.weights}")

    def compute_probability(
        self,
        similarity: float,
        heuristics: dict[str, float],
        skill_overlap: float
    ) -> float:
        """
        Compute overall match probability from components.

        Args:
            similarity: Semantic similarity score (0-1)
            heuristics: Dict of heuristic scores
            skill_overlap: Skill overlap score (0-1)

        Returns:
            Match probability (0-1)
        """
        # Average the heuristic scores
        heuristic_scores = list(heuristics.values())
        avg_heuristic = np.mean(heuristic_scores) if heuristic_scores else 0.5

        # Weighted combination
        probability = (
            self.weights['similarity'] * similarity +
            self.weights['skill_overlap'] * skill_overlap +
            self.weights['heuristics'] * avg_heuristic
        )

        # Ensure probability is between 0 and 1
        probability = max(0.0, min(1.0, probability))

        return float(probability)

    def rank_jobs(
        self,
        user,
        jobs: list,
        embeddings: dict,
        similarity_scorer,
        skill_extractor,
        heuristic_scorer
    ) -> list[tuple]:
        """
        Rank a list of jobs for a user.

        Args:
            user: User model instance
            jobs: List of Job model instances
            embeddings: Dict mapping job IDs to embedding vectors
            similarity_scorer: SimilarityScorer instance
            skill_extractor: SkillExtractor instance
            heuristic_scorer: HeuristicScorer instance

        Returns:
            List of tuples (job, probability, score_breakdown)
            sorted by probability (highest first)
        """
        if not jobs:
            return []

        # Generate user embedding
        user_text = f"{' '.join(user.skills)} {user.resume_text or ''}"

        from app.rag.embeddings import EmbeddingService
        embedding_service = EmbeddingService()
        user_embedding = embedding_service.embed_text(user_text)

        ranked_jobs = []

        for job in jobs:
            try:
                # Get job embedding
                if job.embedding:
                    job_embedding = np.frombuffer(job.embedding, dtype=np.float32)
                else:
                    # Generate if missing
                    job_text = f"{job.title}. {job.description}"
                    job_embedding = embedding_service.embed_text(job_text)

                # Calculate similarity score
                similarity = similarity_scorer.cosine_similarity(user_embedding, job_embedding)

                # Calculate skill overlap
                skill_overlap = similarity_scorer.skill_overlap_score(
                    user.skills,
                    job.skills_extracted
                )

                # Calculate heuristic scores
                heuristics = heuristic_scorer.compute_all(user, job)

                # Compute final probability
                probability = self.compute_probability(
                    similarity=similarity,
                    heuristics=heuristics,
                    skill_overlap=skill_overlap
                )

                # Get matched/missing skills
                matched_skills, missing_skills = similarity_scorer.get_matched_skills(
                    user.skills,
                    job.skills_extracted
                )

                # Build score breakdown
                score_breakdown = {
                    'similarity_score': similarity,
                    'skill_overlap': skill_overlap,
                    'location_score': heuristics.get('location_score', 0.5),
                    'seniority_score': heuristics.get('seniority_score', 0.5),
                    'sector_score': heuristics.get('sector_score', 0.5),
                    'matched_skills': matched_skills,
                    'missing_skills': missing_skills
                }

                ranked_jobs.append((job, probability, score_breakdown))

            except Exception as e:
                logger.error(f"Error ranking job {job.id}: {str(e)}")
                continue

        # Sort by probability (highest first)
        ranked_jobs.sort(key=lambda x: x[1], reverse=True)

        logger.info(f"Ranked {len(ranked_jobs)} jobs for user {user.id}")

        return ranked_jobs

    def explain_score(self, score_breakdown: dict, probability: float) -> dict:
        """
        Generate human-readable explanation of match score.

        Args:
            score_breakdown: Score breakdown dictionary
            probability: Overall match probability

        Returns:
            Dictionary with explanation and recommendations
        """
        explanation = {
            'overall_probability': probability,
            'rating': self._get_rating(probability),
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }

        # Analyze components
        if score_breakdown.get('skill_overlap', 0) > 0.7:
            explanation['strengths'].append(
                f"Strong skill match ({len(score_breakdown.get('matched_skills', []))} skills matched)"
            )
        elif score_breakdown.get('skill_overlap', 0) < 0.3:
            explanation['weaknesses'].append(
                f"Limited skill overlap (missing {len(score_breakdown.get('missing_skills', []))} key skills)"
            )
            explanation['recommendations'].append(
                f"Consider developing: {', '.join(score_breakdown.get('missing_skills', [])[:3])}"
            )

        if score_breakdown.get('seniority_score', 0) > 0.8:
            explanation['strengths'].append("Experience level matches job requirements")
        elif score_breakdown.get('seniority_score', 0) < 0.5:
            explanation['weaknesses'].append("Experience level may not align with role expectations")

        if score_breakdown.get('location_score', 0) > 0.8:
            explanation['strengths'].append("Location is a good fit")
        elif score_breakdown.get('location_score', 0) < 0.6:
            explanation['weaknesses'].append("Location mismatch - may require relocation")

        return explanation

    def _get_rating(self, probability: float) -> str:
        """Get text rating from probability."""
        if probability >= 0.8:
            return "Excellent Match"
        elif probability >= 0.6:
            return "Good Match"
        elif probability >= 0.4:
            return "Moderate Match"
        elif probability >= 0.2:
            return "Weak Match"
        else:
            return "Poor Match"
