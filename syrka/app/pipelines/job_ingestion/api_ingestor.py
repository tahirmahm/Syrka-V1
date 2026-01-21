"""API integration for job aggregators (Adzuna, Reed, etc.)."""

import httpx
from typing import Optional
import logging
from datetime import datetime

from app.config import settings
from app.utils.exceptions import ServiceUnavailableException

logger = logging.getLogger(__name__)


class JobAPIIngestor:
    """
    API client for job aggregation services.

    Supports Adzuna, Reed, and other job APIs with standardized output.
    """

    def __init__(self):
        """Initialize API ingestor with HTTP client."""
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def ingest_from_adzuna(
        self,
        params: dict
    ) -> list[dict]:
        """
        Ingest job postings from Adzuna API.

        Adzuna API docs: https://developer.adzuna.com/overview

        Args:
            params: Query parameters (query, location, results_per_page, page)

        Returns:
            List of job dictionaries

        Raises:
            ServiceUnavailableException: If API is unavailable
        """
        if not settings.ADZUNA_API_KEY or not settings.ADZUNA_APP_ID:
            logger.warning("Adzuna API credentials not configured")
            return []

        jobs = []

        # Adzuna API endpoint (country-specific, using generic example)
        country = params.get('country', 'us')
        base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{params.get('page', 1)}"

        query_params = {
            'app_id': settings.ADZUNA_APP_ID,
            'app_key': settings.ADZUNA_API_KEY,
            'results_per_page': params.get('results_per_page', 20),
            'what': params.get('query', ''),
            'where': params.get('location', ''),
            'content-type': 'application/json'
        }

        try:
            response = await self.client.get(base_url, params=query_params)
            response.raise_for_status()
            data = response.json()

            # Parse Adzuna response format
            for job in data.get('results', []):
                try:
                    job_data = {
                        'title': job.get('title', ''),
                        'company': job.get('company', {}).get('display_name', 'Unknown'),
                        'description': job.get('description', ''),
                        'location': job.get('location', {}).get('display_name', ''),
                        'salary_min': job.get('salary_min'),
                        'salary_max': job.get('salary_max'),
                        'posted_at': self._parse_adzuna_date(job.get('created')),
                        'external_id': str(job.get('id', '')),
                        'source': 'adzuna',
                        'url': job.get('redirect_url', '')
                    }
                    jobs.append(job_data)
                except Exception as e:
                    logger.debug(f"Skipping Adzuna job due to parsing error: {str(e)}")
                    continue

            logger.info(f"Ingested {len(jobs)} jobs from Adzuna")

        except httpx.HTTPStatusError as e:
            logger.error(f"Adzuna API error: {e.response.status_code} - {e.response.text}")
            raise ServiceUnavailableException(f"Adzuna API unavailable: {str(e)}")
        except Exception as e:
            logger.error(f"Adzuna API ingestion failed: {str(e)}")

        return jobs

    async def ingest_from_reed(
        self,
        params: dict
    ) -> list[dict]:
        """
        Ingest job postings from Reed API.

        Reed API docs: https://www.reed.co.uk/developers

        Args:
            params: Query parameters (query, location, resultsToTake)

        Returns:
            List of job dictionaries
        """
        if not settings.REED_API_KEY:
            logger.warning("Reed API credentials not configured")
            return []

        jobs = []
        base_url = "https://www.reed.co.uk/api/1.0/search"

        query_params = {
            'keywords': params.get('query', ''),
            'location': params.get('location', ''),
            'resultsToTake': params.get('results_per_page', 20),
            'resultsToSkip': params.get('skip', 0)
        }

        # Reed uses Basic Auth with API key as username
        auth = (settings.REED_API_KEY, '')

        try:
            response = await self.client.get(
                base_url,
                params=query_params,
                auth=auth
            )
            response.raise_for_status()
            data = response.json()

            # Parse Reed response format
            for job in data.get('results', []):
                try:
                    job_data = {
                        'title': job.get('jobTitle', ''),
                        'company': job.get('employerName', 'Unknown'),
                        'description': job.get('jobDescription', ''),
                        'location': job.get('locationName', ''),
                        'salary_min': job.get('minimumSalary'),
                        'salary_max': job.get('maximumSalary'),
                        'posted_at': self._parse_reed_date(job.get('date')),
                        'external_id': str(job.get('jobId', '')),
                        'source': 'reed',
                        'url': job.get('jobUrl', '')
                    }
                    jobs.append(job_data)
                except Exception as e:
                    logger.debug(f"Skipping Reed job due to parsing error: {str(e)}")
                    continue

            logger.info(f"Ingested {len(jobs)} jobs from Reed")

        except httpx.HTTPStatusError as e:
            logger.error(f"Reed API error: {e.response.status_code} - {e.response.text}")
            raise ServiceUnavailableException(f"Reed API unavailable: {str(e)}")
        except Exception as e:
            logger.error(f"Reed API ingestion failed: {str(e)}")

        return jobs

    async def ingest_from_github_jobs(
        self,
        params: dict
    ) -> list[dict]:
        """
        Ingest tech job postings from GitHub Jobs API (deprecated but shown as example).

        Args:
            params: Query parameters

        Returns:
            List of job dictionaries
        """
        jobs = []
        base_url = "https://jobs.github.com/positions.json"

        query_params = {
            'description': params.get('query', ''),
            'location': params.get('location', ''),
            'page': params.get('page', 0)
        }

        try:
            response = await self.client.get(base_url, params=query_params)
            response.raise_for_status()
            data = response.json()

            for job in data:
                try:
                    job_data = {
                        'title': job.get('title', ''),
                        'company': job.get('company', 'Unknown'),
                        'description': job.get('description', ''),
                        'location': job.get('location', ''),
                        'posted_at': self._parse_iso_date(job.get('created_at')),
                        'external_id': job.get('id', ''),
                        'source': 'github_jobs',
                        'url': job.get('url', '')
                    }
                    jobs.append(job_data)
                except Exception as e:
                    logger.debug(f"Skipping GitHub job: {str(e)}")
                    continue

            logger.info(f"Ingested {len(jobs)} jobs from GitHub Jobs")

        except Exception as e:
            logger.error(f"GitHub Jobs ingestion failed: {str(e)}")

        return jobs

    async def ingest(
        self,
        source: str,
        params: dict
    ) -> list[dict]:
        """
        Generic ingestion method that routes to specific API integrations.

        Args:
            source: API source name ('adzuna', 'reed', etc.)
            params: Query parameters

        Returns:
            List of job dictionaries with standardized format
        """
        source = source.lower()

        if source == 'adzuna':
            return await self.ingest_from_adzuna(params)
        elif source == 'reed':
            return await self.ingest_from_reed(params)
        elif source == 'github_jobs':
            return await self.ingest_from_github_jobs(params)
        else:
            logger.warning(f"Unknown API source: {source}")
            return []

    def _parse_adzuna_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Adzuna date format."""
        if not date_str:
            return None
        try:
            # Adzuna uses ISO 8601 format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None

    def _parse_reed_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Reed date format."""
        if not date_str:
            return None
        try:
            # Reed typically uses format like "2023-12-25T10:30:00"
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None

    def _parse_iso_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO 8601 date format."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None
