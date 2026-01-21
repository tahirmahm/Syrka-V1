"""Job ingestion pipeline orchestrator."""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np

from app.pipelines.job_ingestion.scraper import JobScraper
from app.pipelines.job_ingestion.api_ingestor import JobAPIIngestor
from app.pipelines.job_ingestion.normalizer import JobNormalizer
from app.models.job import Job
from app.rag.embeddings import EmbeddingService
from app.matching.skill_extractor import SkillExtractor

logger = logging.getLogger(__name__)


class JobIngestionOrchestrator:
    """
    Orchestrates the complete job ingestion pipeline.

    Coordinates scraping, API ingestion, normalization, skill extraction,
    embedding generation, and database storage.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        skill_extractor: SkillExtractor
    ):
        """
        Initialize ingestion orchestrator.

        Args:
            embedding_service: Service for generating embeddings
            skill_extractor: Service for extracting skills
        """
        self.scraper = JobScraper()
        self.api_ingestor = JobAPIIngestor()
        self.normalizer = JobNormalizer()
        self.embedding_service = embedding_service
        self.skill_extractor = skill_extractor

    async def close(self) -> None:
        """Close HTTP clients."""
        await self.scraper.close()
        await self.api_ingestor.close()

    async def run_full_ingestion(
        self,
        sources: list[str],
        params: dict,
        db: AsyncSession
    ) -> int:
        """
        Run complete ingestion pipeline for multiple sources.

        Args:
            sources: List of source names ('linkedin', 'indeed', 'adzuna', etc.)
            params: Query parameters (query, location, limit, etc.)
            db: Database session

        Returns:
            Number of jobs successfully ingested
        """
        total_ingested = 0

        for source in sources:
            try:
                logger.info(f"Starting ingestion from {source}")

                # Fetch raw jobs
                if source in ['linkedin', 'indeed']:
                    raw_jobs = await self.scraper.scrape(source, params)
                elif source in ['adzuna', 'reed', 'github_jobs']:
                    raw_jobs = await self.api_ingestor.ingest(source, params)
                else:
                    logger.warning(f"Unknown source: {source}")
                    continue

                if not raw_jobs:
                    logger.info(f"No jobs fetched from {source}")
                    continue

                # Normalize jobs
                normalized_jobs = self.normalizer.batch_normalize(raw_jobs, source)

                # Process each job
                for job_data in normalized_jobs:
                    try:
                        job = await self.process_single_job(job_data, db)
                        if job:
                            total_ingested += 1
                    except Exception as e:
                        logger.error(f"Failed to process job: {str(e)}")
                        continue

                logger.info(f"Completed ingestion from {source}: {len(normalized_jobs)} jobs")

            except Exception as e:
                logger.error(f"Ingestion from {source} failed: {str(e)}")
                continue

        logger.info(f"Total jobs ingested: {total_ingested}")
        return total_ingested

    async def process_single_job(
        self,
        job_data: dict,
        db: AsyncSession
    ) -> Optional[Job]:
        """
        Process a single job through the complete pipeline.

        Args:
            job_data: Normalized job dictionary
            db: Database session

        Returns:
            Created Job object or None if failed/duplicate
        """
        # Check for duplicates by external_id
        external_id = job_data.get('external_id')
        if external_id:
            stmt = select(Job).where(Job.external_id == external_id)
            result = await db.execute(stmt)
            existing_job = result.scalar_one_or_none()

            if existing_job:
                logger.debug(f"Job already exists: {external_id}")
                return None

        # Extract skills
        job_text = f"{job_data.get('title', '')} {job_data.get('description', '')} {job_data.get('requirements', '')}"
        skills = self.skill_extractor.extract_from_text(job_text)
        job_data['skills_extracted'] = skills

        # Generate embedding for semantic search
        embedding_text = f"{job_data.get('title', '')}. {job_data.get('description', '')}"
        embedding = self.embedding_service.embed_text(embedding_text)
        job_data['embedding'] = embedding.tobytes()  # Store as bytes

        # Create Job object
        job = Job(**job_data)

        # Save to database
        db.add(job)
        await db.flush()  # Flush to get ID without committing
        await db.refresh(job)

        logger.debug(f"Ingested job: {job.title} at {job.company}")
        return job

    async def reindex_existing_jobs(
        self,
        db: AsyncSession,
        batch_size: int = 100
    ) -> int:
        """
        Reindex existing jobs (regenerate embeddings and skills).

        Useful after model updates or skill taxonomy changes.

        Args:
            db: Database session
            batch_size: Number of jobs to process at once

        Returns:
            Number of jobs reindexed
        """
        total_reindexed = 0
        offset = 0

        while True:
            # Fetch batch of jobs
            stmt = select(Job).offset(offset).limit(batch_size)
            result = await db.execute(stmt)
            jobs = result.scalars().all()

            if not jobs:
                break

            for job in jobs:
                try:
                    # Re-extract skills
                    job_text = f"{job.title} {job.description} {job.requirements or ''}"
                    skills = self.skill_extractor.extract_from_text(job_text)
                    job.skills_extracted = skills

                    # Regenerate embedding
                    embedding_text = f"{job.title}. {job.description}"
                    embedding = self.embedding_service.embed_text(embedding_text)
                    job.embedding = embedding.tobytes()

                    total_reindexed += 1

                except Exception as e:
                    logger.error(f"Failed to reindex job {job.id}: {str(e)}")
                    continue

            await db.flush()
            offset += batch_size
            logger.info(f"Reindexed {total_reindexed} jobs so far...")

        logger.info(f"Total jobs reindexed: {total_reindexed}")
        return total_reindexed

    async def deactivate_old_jobs(
        self,
        db: AsyncSession,
        days_old: int = 30
    ) -> int:
        """
        Deactivate jobs older than specified days.

        Args:
            db: Database session
            days_old: Number of days to consider a job as old

        Returns:
            Number of jobs deactivated
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        stmt = select(Job).where(
            Job.posted_at < cutoff_date,
            Job.is_active == True
        )
        result = await db.execute(stmt)
        old_jobs = result.scalars().all()

        count = 0
        for job in old_jobs:
            job.is_active = False
            count += 1

        await db.flush()
        logger.info(f"Deactivated {count} jobs older than {days_old} days")
        return count
