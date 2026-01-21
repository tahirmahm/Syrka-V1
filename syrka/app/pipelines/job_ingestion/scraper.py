"""Web scraping for job postings from various sources."""

import httpx
from bs4 import BeautifulSoup
from typing import Optional
import logging
import asyncio
from datetime import datetime

from app.config import settings
from app.utils.exceptions import ServiceUnavailableException, RateLimitException

logger = logging.getLogger(__name__)


class JobScraper:
    """
    Web scraper for job postings from multiple sources.

    Handles rate limiting, retries, and parsing of job data.
    """

    def __init__(self):
        """Initialize job scraper with HTTP client."""
        self.client = httpx.AsyncClient(
            headers={'User-Agent': settings.SCRAPER_USER_AGENT},
            timeout=30.0,
            follow_redirects=True
        )
        self.rate_limit = settings.SCRAPER_RATE_LIMIT
        self.max_retries = settings.SCRAPER_MAX_RETRIES

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def _rate_limited_request(self, url: str, retries: int = 0) -> Optional[httpx.Response]:
        """
        Make rate-limited HTTP request with retry logic.

        Args:
            url: URL to fetch
            retries: Current retry attempt

        Returns:
            Response object or None if failed
        """
        try:
            # Rate limiting delay
            await asyncio.sleep(self.rate_limit)

            response = await self.client.get(url)
            response.raise_for_status()
            return response

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and retries < self.max_retries:
                # Rate limited, retry with exponential backoff
                wait_time = (2 ** retries) * self.rate_limit
                logger.warning(f"Rate limited, waiting {wait_time}s before retry {retries + 1}")
                await asyncio.sleep(wait_time)
                return await self._rate_limited_request(url, retries + 1)
            else:
                logger.error(f"HTTP error fetching {url}: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None

    async def scrape_linkedin_jobs(
        self,
        query: str,
        location: str = "",
        limit: int = 20
    ) -> list[dict]:
        """
        Scrape job postings from LinkedIn.

        Note: This is a simplified implementation. Production scraping would need
        to handle LinkedIn's authentication and anti-scraping measures.

        Args:
            query: Search query (job title, keywords)
            location: Location filter
            limit: Maximum number of jobs to scrape

        Returns:
            List of job dictionaries with extracted data
        """
        jobs = []

        # LinkedIn Jobs URL format (simplified - actual implementation would be more complex)
        base_url = "https://www.linkedin.com/jobs/search/"
        params = {
            'keywords': query,
            'location': location,
            'start': 0
        }

        try:
            # Build URL with query parameters
            url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

            response = await self._rate_limited_request(url)
            if not response:
                return jobs

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find job cards (selectors would need to be updated based on actual LinkedIn HTML)
            job_cards = soup.find_all('div', class_='job-card-container', limit=limit)

            for card in job_cards:
                try:
                    job_data = {
                        'title': card.find('h3', class_='job-card-title').get_text(strip=True),
                        'company': card.find('h4', class_='job-card-company').get_text(strip=True),
                        'location': card.find('span', class_='job-card-location').get_text(strip=True),
                        'description': card.find('div', class_='job-card-description').get_text(strip=True),
                        'posted_at': self._parse_posted_date(
                            card.find('time', class_='job-card-date').get_text(strip=True)
                        ),
                        'external_id': card.get('data-job-id', ''),
                        'source': 'linkedin'
                    }
                    jobs.append(job_data)
                except AttributeError as e:
                    # Skip jobs with missing required fields
                    logger.debug(f"Skipping job card due to missing field: {str(e)}")
                    continue

            logger.info(f"Scraped {len(jobs)} jobs from LinkedIn")

        except Exception as e:
            logger.error(f"LinkedIn scraping failed: {str(e)}")

        return jobs

    async def scrape_indeed_jobs(
        self,
        query: str,
        location: str = "",
        limit: int = 20
    ) -> list[dict]:
        """
        Scrape job postings from Indeed.

        Args:
            query: Search query
            location: Location filter
            limit: Maximum number of jobs

        Returns:
            List of job dictionaries
        """
        jobs = []

        # Indeed URL format
        base_url = "https://www.indeed.com/jobs"
        params = {
            'q': query,
            'l': location,
            'start': 0
        }

        try:
            url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

            response = await self._rate_limited_request(url)
            if not response:
                return jobs

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find job cards (selectors are examples - would need verification)
            job_cards = soup.find_all('div', class_='job_seen_beacon', limit=limit)

            for card in job_cards:
                try:
                    title_elem = card.find('h2', class_='jobTitle')
                    company_elem = card.find('span', class_='companyName')
                    location_elem = card.find('div', class_='companyLocation')

                    if not all([title_elem, company_elem]):
                        continue

                    # Extract job link for full description
                    job_link = title_elem.find('a')
                    job_url = f"https://www.indeed.com{job_link['href']}" if job_link else None

                    job_data = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True),
                        'location': location_elem.get_text(strip=True) if location_elem else location,
                        'description': card.find('div', class_='job-snippet').get_text(strip=True) if card.find('div', class_='job-snippet') else '',
                        'external_id': job_link.get('data-jk', '') if job_link else '',
                        'source': 'indeed',
                        'url': job_url
                    }

                    jobs.append(job_data)

                except Exception as e:
                    logger.debug(f"Skipping job card: {str(e)}")
                    continue

            logger.info(f"Scraped {len(jobs)} jobs from Indeed")

        except Exception as e:
            logger.error(f"Indeed scraping failed: {str(e)}")

        return jobs

    async def scrape(
        self,
        source: str,
        params: dict
    ) -> list[dict]:
        """
        Generic scraping method that routes to specific scrapers.

        Args:
            source: Source name ('linkedin', 'indeed', etc.)
            params: Scraping parameters (query, location, limit)

        Returns:
            List of scraped job dictionaries
        """
        query = params.get('query', '')
        location = params.get('location', '')
        limit = params.get('limit', 20)

        if source.lower() == 'linkedin':
            return await self.scrape_linkedin_jobs(query, location, limit)
        elif source.lower() == 'indeed':
            return await self.scrape_indeed_jobs(query, location, limit)
        else:
            logger.warning(f"Unknown scraping source: {source}")
            return []

    def _parse_posted_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse posted date string to datetime.

        Args:
            date_str: Date string (e.g., "2 days ago", "1 week ago")

        Returns:
            Datetime object or None
        """
        # Simplified date parsing - production would need more robust parsing
        from datetime import timedelta

        now = datetime.utcnow()
        date_str = date_str.lower()

        try:
            if 'hour' in date_str or 'hours' in date_str:
                hours = int(''.join(filter(str.isdigit, date_str)) or 1)
                return now - timedelta(hours=hours)
            elif 'day' in date_str or 'days' in date_str:
                days = int(''.join(filter(str.isdigit, date_str)) or 1)
                return now - timedelta(days=days)
            elif 'week' in date_str or 'weeks' in date_str:
                weeks = int(''.join(filter(str.isdigit, date_str)) or 1)
                return now - timedelta(weeks=weeks)
            elif 'month' in date_str or 'months' in date_str:
                months = int(''.join(filter(str.isdigit, date_str)) or 1)
                return now - timedelta(days=months * 30)
            else:
                return now
        except:
            return now
