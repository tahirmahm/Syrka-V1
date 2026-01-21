"""Job data normalization and standardization."""

import re
from typing import Optional, tuple
import logging
from datetime import datetime

from app.utils.helpers import parse_salary_range, clean_text

logger = logging.getLogger(__name__)


class JobNormalizer:
    """
    Normalizes job data from various sources into a standardized format.

    Handles field mapping, data cleaning, and value extraction.
    """

    # Seniority level keywords
    SENIORITY_KEYWORDS = {
        'junior': ['junior', 'entry level', 'graduate', 'associate', 'jr.'],
        'mid': ['mid level', 'intermediate', 'experienced'],
        'senior': ['senior', 'sr.', 'lead', 'principal', 'staff'],
        'executive': ['director', 'vp', 'chief', 'head of', 'executive']
    }

    # Sector keywords for classification
    SECTOR_KEYWORDS = {
        'Technology': ['software', 'developer', 'engineer', 'IT', 'tech', 'data', 'ai', 'ml', 'devops', 'cloud'],
        'Healthcare': ['healthcare', 'medical', 'nurse', 'doctor', 'clinical', 'hospital', 'pharmaceutical'],
        'Finance': ['finance', 'banking', 'accounting', 'investment', 'financial', 'analyst'],
        'Education': ['teacher', 'education', 'academic', 'professor', 'instructor', 'training'],
        'Manufacturing': ['manufacturing', 'production', 'factory', 'industrial', 'assembly'],
        'Construction': ['construction', 'building', 'contractor', 'architect', 'civil'],
        'Retail': ['retail', 'sales', 'store', 'merchandising', 'customer service']
    }

    def normalize(self, raw_job: dict, source: str) -> dict:
        """
        Normalize a raw job dictionary into standardized format.

        Args:
            raw_job: Raw job data from scraper or API
            source: Source name for source-specific normalization

        Returns:
            Normalized job dictionary ready for database insertion
        """
        normalized = {
            'external_id': self._extract_external_id(raw_job, source),
            'title': clean_text(raw_job.get('title', '')),
            'company': clean_text(raw_job.get('company', 'Unknown')),
            'description': clean_text(raw_job.get('description', '')),
            'requirements': self._extract_requirements(raw_job),
            'location': clean_text(raw_job.get('location', '')),
            'sector': self.extract_sector(raw_job.get('description', ''), raw_job.get('company', '')),
            'seniority_level': self.extract_seniority(raw_job.get('title', ''), raw_job.get('description', '')),
            'salary_min': None,
            'salary_max': None,
            'source': source,
            'posted_at': raw_job.get('posted_at') or datetime.utcnow()
        }

        # Extract salary range
        salary_min, salary_max = self._extract_salary(raw_job)
        normalized['salary_min'] = salary_min
        normalized['salary_max'] = salary_max

        return normalized

    def _extract_external_id(self, raw_job: dict, source: str) -> str:
        """
        Extract or generate external ID for deduplication.

        Args:
            raw_job: Raw job data
            source: Source name

        Returns:
            External ID string
        """
        external_id = raw_job.get('external_id', '')

        if external_id:
            return f"{source}_{external_id}"

        # Generate ID from title + company + location if no external ID
        from app.utils.helpers import generate_hash
        unique_string = f"{raw_job.get('title', '')}_{raw_job.get('company', '')}_{raw_job.get('location', '')}"
        return f"{source}_{generate_hash(unique_string)[:16]}"

    def _extract_requirements(self, raw_job: dict) -> Optional[str]:
        """
        Extract requirements section from job description.

        Args:
            raw_job: Raw job data

        Returns:
            Requirements text or None
        """
        description = raw_job.get('description', '')

        # Look for common requirements section headers
        requirements_patterns = [
            r'requirements:(.+?)(?=responsibilities:|qualifications:|$)',
            r'qualifications:(.+?)(?=responsibilities:|requirements:|$)',
            r'what you\'ll need:(.+?)(?=what you\'ll do:|responsibilities:|$)',
            r'must have:(.+?)(?=nice to have:|responsibilities:|$)'
        ]

        for pattern in requirements_patterns:
            match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
            if match:
                return clean_text(match.group(1))

        # If no specific section, return None (will use full description)
        return None

    def _extract_salary(self, raw_job: dict) -> tuple[Optional[int], Optional[int]]:
        """
        Extract salary range from job data.

        Args:
            raw_job: Raw job data

        Returns:
            Tuple of (min_salary, max_salary)
        """
        # Check if salary fields are already present
        salary_min = raw_job.get('salary_min')
        salary_max = raw_job.get('salary_max')

        if salary_min and salary_max:
            return (salary_min, salary_max)

        # Try to parse from description
        description = raw_job.get('description', '')
        title = raw_job.get('title', '')
        combined_text = f"{title} {description}"

        # Look for salary mentions
        salary_patterns = [
            r'\$[\d,]+\s*-\s*\$[\d,]+',
            r'£[\d,]+\s*-\s*£[\d,]+',
            r'€[\d,]+\s*-\s*€[\d,]+',
            r'\d+k\s*-\s*\d+k',
        ]

        for pattern in salary_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                return parse_salary_range(match.group(0))

        return (None, None)

    def extract_seniority(self, title: str, description: str) -> str:
        """
        Extract seniority level from job title and description.

        Args:
            title: Job title
            description: Job description

        Returns:
            Seniority level: junior/mid/senior/executive
        """
        combined_text = f"{title} {description}".lower()

        # Check for seniority keywords (prioritize title over description)
        title_lower = title.lower()

        for level, keywords in self.SENIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return level

        # Check description if not found in title
        for level, keywords in self.SENIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined_text:
                    return level

        # Default to mid level if unclear
        return 'mid'

    def extract_sector(self, description: str, company: str) -> str:
        """
        Extract industry sector from description and company name.

        Args:
            description: Job description
            company: Company name

        Returns:
            Sector name
        """
        combined_text = f"{description} {company}".lower()

        # Score each sector by keyword matches
        sector_scores = {}
        for sector, keywords in self.SECTOR_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                sector_scores[sector] = score

        # Return sector with highest score
        if sector_scores:
            return max(sector_scores.items(), key=lambda x: x[1])[0]

        # Default to general if no clear sector
        return 'General'

    def batch_normalize(self, raw_jobs: list[dict], source: str) -> list[dict]:
        """
        Normalize a batch of jobs.

        Args:
            raw_jobs: List of raw job dictionaries
            source: Source name

        Returns:
            List of normalized job dictionaries
        """
        normalized_jobs = []

        for raw_job in raw_jobs:
            try:
                normalized = self.normalize(raw_job, source)
                normalized_jobs.append(normalized)
            except Exception as e:
                logger.error(f"Failed to normalize job: {str(e)}")
                continue

        logger.info(f"Normalized {len(normalized_jobs)} out of {len(raw_jobs)} jobs from {source}")
        return normalized_jobs
