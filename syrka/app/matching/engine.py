"""Unified job matching engine."""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np

from app.models.user import User
from app.models.job import Job
from app.matching.skill_extractor import SkillExtractor
from app.matching.similarity import SimilarityScorer
from app.matching.heuristics import HeuristicScorer
from app.matching.ranker import JobRanker
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import FAISSVectorStore
from app.config import settings

logger = logging.getLogger(__name__)


class MatchingEngine:
    """
    Unified matching engine for job-candidate matching.

    Combines all matching components to provide complete matching functionality.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: Optional[FAISSVectorStore] = None,
        skill_extractor: Optional[SkillExtractor] = None,
        heuristic_scorer: Optional[HeuristicScorer] = None,
        ranker: Optional[JobRanker] = None
    ):
        """
        Initialize matching engine.

        Args:
            embedding_service: Service for generating embeddings
            vector_store: Optional vector store for fast similarity search
            skill_extractor: Optional skill extractor
            heuristic_scorer: Optional heuristic scorer
            ranker: Optional job ranker
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store

        # Initialize components
        self.skill_extractor = skill_extractor or SkillExtractor()
        self.similarity_scorer = SimilarityScorer(embedding_service)
        self.heuristic_scorer = heuristic_scorer or HeuristicScorer()
        self.ranker = ranker or JobRanker()

    async def match(
        self,
        user: User,
        db: AsyncSession,
        limit: int = 20,
        filters: Optional[dict] = None,
        min_probability: float = 0.0
    ) -> list[dict]:
        """
        Find matching jobs for a user.

        Args:
            user: User to match
            db: Database session
            limit: Maximum number of matches to return
            filters: Optional filters (sector, location, etc.)
            min_probability: Minimum match probability threshold

        Returns:
            List of match result dictionaries
        """
        logger.info(f"Finding matches for user {user.id}")

        # Build query for active jobs
        stmt = select(Job).where(Job.is_active == True)

        # Apply filters
        if filters:
            if 'sector' in filters and filters['sector']:
                stmt = stmt.where(Job.sector == filters['sector'])
            if 'location' in filters and filters['location']:
                stmt = stmt.where(Job.location.contains(filters['location']))
            if 'seniority_level' in filters and filters['seniority_level']:
                stmt = stmt.where(Job.seniority_level == filters['seniority_level'])

        # Limit to reasonable number for processing
        stmt = stmt.limit(min(limit * 5, 500))

        result = await db.execute(stmt)
        candidate_jobs = result.scalars().all()

        if not candidate_jobs:
            logger.info("No candidate jobs found")
            return []

        # Rank jobs
        ranked_jobs = self.ranker.rank_jobs(
            user=user,
            jobs=candidate_jobs,
            embeddings={},
            similarity_scorer=self.similarity_scorer,
            skill_extractor=self.skill_extractor,
            heuristic_scorer=self.heuristic_scorer
        )

        # Filter by minimum probability and limit
        matches = []
        for job, probability, breakdown in ranked_jobs:
            if probability >= min_probability and len(matches) < limit:
                match_result = {
                    'job': job,
                    'match_probability': probability,
                    'scores': {
                        'similarity_score': breakdown['similarity_score'],
                        'skill_overlap': breakdown['skill_overlap'],
                        'location_score': breakdown['location_score'],
                        'seniority_score': breakdown['seniority_score'],
                        'sector_score': breakdown['sector_score']
                    },
                    'matched_skills': breakdown['matched_skills'],
                    'missing_skills': breakdown['missing_skills']
                }
                matches.append(match_result)

        logger.info(f"Found {len(matches)} matches for user {user.id}")

        return matches

    async def explain_match(
        self,
        user: User,
        job: Job,
        db: AsyncSession
    ) -> dict:
        """
        Generate detailed explanation of match between user and job.

        Args:
            user: User instance
            job: Job instance
            db: Database session

        Returns:
            Detailed match explanation dictionary
        """
        # Generate embeddings
        user_text = f"{' '.join(user.skills)} {user.resume_text or ''}"
        user_embedding = self.embedding_service.embed_text(user_text)

        if job.embedding:
            job_embedding = np.frombuffer(job.embedding, dtype=np.float32)
        else:
            job_text = f"{job.title}. {job.description}"
            job_embedding = self.embedding_service.embed_text(job_text)

        # Calculate all scores
        similarity = self.similarity_scorer.cosine_similarity(user_embedding, job_embedding)
        skill_overlap = self.similarity_scorer.skill_overlap_score(user.skills, job.skills_extracted)
        heuristics = self.heuristic_scorer.compute_all(user, job)

        # Get matched/missing skills
        matched_skills, missing_skills = self.similarity_scorer.get_matched_skills(
            user.skills,
            job.skills_extracted
        )

        # Calculate probability
        probability = self.ranker.compute_probability(similarity, heuristics, skill_overlap)

        # Build breakdown
        score_breakdown = {
            'similarity_score': similarity,
            'skill_overlap': skill_overlap,
            'location_score': heuristics['location_score'],
            'seniority_score': heuristics['seniority_score'],
            'sector_score': heuristics['sector_score'],
            'matched_skills': matched_skills,
            'missing_skills': missing_skills
        }

        # Generate explanation
        explanation = self.ranker.explain_score(score_breakdown, probability)

        # Combine into full result
        result = {
            'job_id': job.id,
            'user_id': user.id,
            'match_probability': probability,
            'scores': score_breakdown,
            'explanation': explanation
        }

        return result

    async def bulk_match(
        self,
        user_ids: list[str],
        db: AsyncSession,
        limit_per_user: int = 10
    ) -> dict[str, list[dict]]:
        """
        Perform bulk matching for multiple users.

        Args:
            user_ids: List of user IDs
            db: Database session
            limit_per_user: Max matches per user

        Returns:
            Dictionary mapping user IDs to their match lists
        """
        results = {}

        for user_id in user_ids:
            try:
                # Fetch user
                stmt = select(User).where(User.id == user_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if not user:
                    logger.warning(f"User not found: {user_id}")
                    continue

                # Get matches
                matches = await self.match(user, db, limit=limit_per_user)
                results[str(user_id)] = matches

            except Exception as e:
                logger.error(f"Error matching user {user_id}: {str(e)}")
                results[str(user_id)] = []

        logger.info(f"Completed bulk matching for {len(user_ids)} users")

        return results

    async def get_similar_jobs(
        self,
        job: Job,
        db: AsyncSession,
        limit: int = 10
    ) -> list[Job]:
        """
        Find jobs similar to a given job.

        Args:
            job: Reference job
            db: Database session
            limit: Number of similar jobs to return

        Returns:
            List of similar Job instances
        """
        if not job.embedding:
            return []

        job_embedding = np.frombuffer(job.embedding, dtype=np.float32)

        # Fetch all active jobs
        stmt = select(Job).where(
            Job.is_active == True,
            Job.id != job.id
        ).limit(500)

        result = await db.execute(stmt)
        candidate_jobs = result.scalars().all()

        # Calculate similarities
        job_similarities = []
        for candidate in candidate_jobs:
            if candidate.embedding:
                cand_embedding = np.frombuffer(candidate.embedding, dtype=np.float32)
                similarity = self.similarity_scorer.cosine_similarity(job_embedding, cand_embedding)
                job_similarities.append((candidate, similarity))

        # Sort by similarity
        job_similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top jobs
        similar_jobs = [job for job, _ in job_similarities[:limit]]

        logger.info(f"Found {len(similar_jobs)} similar jobs to {job.id}")

        return similar_jobs
