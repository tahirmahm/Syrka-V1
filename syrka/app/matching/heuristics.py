"""Heuristic scoring for job matching based on non-embedding features."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class HeuristicScorer:
    """
    Calculate heuristic match scores based on location, seniority, sector, etc.

    Provides interpretable scoring components to complement semantic similarity.
    """

    # Seniority level hierarchy for comparison
    SENIORITY_LEVELS = {
        'junior': 1,
        'mid': 2,
        'senior': 3,
        'executive': 4
    }

    def location_score(self, user_location: Optional[str], job_location: Optional[str]) -> float:
        """
        Calculate location match score.

        Args:
            user_location: User's location/region
            job_location: Job's location/region

        Returns:
            Location score (0 to 1)
                1.0 = exact match or remote
                0.8 = same region/country
                0.5 = different but possible
                0.0 = incompatible (if strict location)
        """
        if not job_location or not user_location:
            return 0.7  # Neutral score if location not specified

        user_loc = user_location.lower().strip()
        job_loc = job_location.lower().strip()

        # Exact match
        if user_loc == job_loc:
            return 1.0

        # Remote/hybrid jobs
        if 'remote' in job_loc or 'hybrid' in job_loc:
            return 1.0

        # Same city/region (simplified - production would use geocoding)
        user_parts = set(user_loc.split(','))
        job_parts = set(job_loc.split(','))

        overlap = len(user_parts & job_parts)
        if overlap > 0:
            return 0.8

        # Different locations
        return 0.5  # Still possible for relocation

    def seniority_score(
        self,
        user_experience: int,
        job_seniority: Optional[str]
    ) -> float:
        """
        Calculate seniority match score.

        Args:
            user_experience: User's years of experience
            job_seniority: Job's seniority level (junior/mid/senior/executive)

        Returns:
            Seniority score (0 to 1)
        """
        if not job_seniority:
            return 0.8  # Neutral if seniority not specified

        job_level = self.SENIORITY_LEVELS.get(job_seniority.lower(), 2)

        # Estimate user's level from experience
        if user_experience < 2:
            user_level = 1  # junior
        elif user_experience < 5:
            user_level = 2  # mid
        elif user_experience < 10:
            user_level = 3  # senior
        else:
            user_level = 4  # executive

        # Perfect match
        if user_level == job_level:
            return 1.0

        # One level difference
        if abs(user_level - job_level) == 1:
            # Slight preference for being slightly overqualified
            if user_level > job_level:
                return 0.9
            else:
                return 0.7

        # Two levels difference
        if abs(user_level - job_level) == 2:
            return 0.5

        # More than 2 levels - poor match
        return 0.3

    def sector_score(
        self,
        user_sector: Optional[str],
        job_sector: Optional[str]
    ) -> float:
        """
        Calculate sector match score.

        Args:
            user_sector: User's preferred sector
            job_sector: Job's sector

        Returns:
            Sector score (0 to 1)
        """
        if not user_sector or not job_sector:
            return 0.7  # Neutral if not specified

        user_sec = user_sector.lower().strip()
        job_sec = job_sector.lower().strip()

        # Exact match
        if user_sec == job_sec:
            return 1.0

        # Partial match (e.g., "tech" in "fintech")
        if user_sec in job_sec or job_sec in user_sec:
            return 0.8

        # Related sectors (simplified - production would have sector taxonomy)
        related_sectors = {
            'technology': ['software', 'it', 'tech', 'data'],
            'finance': ['banking', 'fintech', 'investment'],
            'healthcare': ['medical', 'pharmaceutical', 'biotech']
        }

        for category, sectors in related_sectors.items():
            if (user_sec in sectors or user_sec == category) and \
               (job_sec in sectors or job_sec == category):
                return 0.7

        # Different sectors - user might be open to change
        return 0.4

    def salary_score(
        self,
        user_expectation: Optional[int],
        job_salary_range: tuple[Optional[int], Optional[int]]
    ) -> float:
        """
        Calculate salary match score.

        Args:
            user_expectation: User's expected salary
            job_salary_range: Tuple of (min_salary, max_salary)

        Returns:
            Salary score (0 to 1)
        """
        if not user_expectation or not any(job_salary_range):
            return 0.8  # Neutral if salary not specified

        salary_min, salary_max = job_salary_range

        # Use average if range is specified
        if salary_min and salary_max:
            job_salary = (salary_min + salary_max) / 2
        elif salary_min:
            job_salary = salary_min
        elif salary_max:
            job_salary = salary_max
        else:
            return 0.8

        # Calculate ratio
        ratio = job_salary / user_expectation

        # Ideal: job pays 100-120% of expectation
        if 1.0 <= ratio <= 1.2:
            return 1.0

        # Acceptable: 80-140% of expectation
        if 0.8 <= ratio <= 1.4:
            return 0.8

        # Below expectation but might be acceptable
        if 0.6 <= ratio < 0.8:
            return 0.5

        # Well below expectation
        if ratio < 0.6:
            return 0.2

        # Significantly above expectation (user might be underqualified)
        if ratio > 1.4:
            return 0.6

        return 0.5

    def compute_all(self, user, job) -> dict[str, float]:
        """
        Compute all heuristic scores for a user-job pair.

        Args:
            user: User model instance
            job: Job model instance

        Returns:
            Dictionary of all heuristic scores
        """
        scores = {
            'location_score': self.location_score(
                user.location,
                job.location
            ),
            'seniority_score': self.seniority_score(
                user.experience_years,
                job.seniority_level
            ),
            'sector_score': self.sector_score(
                user.sector_preference,
                job.sector
            ),
            'salary_score': self.salary_score(
                None,  # User salary expectation (not in current model)
                (job.salary_min, job.salary_max)
            )
        }

        return scores
