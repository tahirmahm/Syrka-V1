"""Job application automation orchestrator."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from app.models.application import Application, ApplicationStatus
from app.automation.gmail_client import GmailClient
from app.automation.cv_generator import CVGenerator
from app.automation.cover_letter_generator import CoverLetterGenerator

logger = logging.getLogger(__name__)


class ApplicationAutomator:
    """Automate job application process end-to-end."""

    def __init__(
        self,
        gmail_client: Optional[GmailClient] = None,
        cv_generator: Optional[CVGenerator] = None,
        cover_letter_generator: Optional[CoverLetterGenerator] = None
    ):
        """
        Initialize application automator.

        Args:
            gmail_client: Gmail client for sending emails
            cv_generator: CV generator
            cover_letter_generator: Cover letter generator
        """
        self.gmail_client = gmail_client or GmailClient()
        self.cv_generator = cv_generator or CVGenerator()
        self.cover_letter_generator = cover_letter_generator or CoverLetterGenerator()

    async def prepare_application(
        self,
        user,
        job,
        db: AsyncSession
    ) -> Application:
        """
        Prepare application materials (CV and cover letter).

        Args:
            user: User model instance
            job: Job model instance
            db: Database session

        Returns:
            Application object in draft status
        """
        logger.info(f"Preparing application for user {user.id} to job {job.id}")

        # Generate tailored CV
        cv = self.cv_generator.tailor_cv(user, job)

        # Generate cover letter
        cover_letter = self.cover_letter_generator.generate(user, job)

        # Create application record
        application = Application(
            user_id=user.id,
            job_id=job.id,
            status=ApplicationStatus.DRAFT.value,
            tailored_cv=cv,
            cover_letter=cover_letter
        )

        db.add(application)
        await db.flush()
        await db.refresh(application)

        logger.info(f"Application prepared: {application.id}")

        return application

    async def send_application(
        self,
        application: Application,
        db: AsyncSession
    ) -> Application:
        """
        Send application via email.

        Args:
            application: Application instance
            db: Database session

        Returns:
            Updated application
        """
        logger.info(f"Sending application {application.id}")

        # Build email
        subject = f"Application for {application.job.title}"
        body = f"""{application.cover_letter}

---
CV attached.

{application.tailored_cv}
"""

        # Send email
        # Note: In production, would need actual recruiter email from job posting
        recruiter_email = "recruiter@example.com"  # Placeholder

        message_id = self.gmail_client.send_email(
            to=recruiter_email,
            subject=subject,
            body=body
        )

        if message_id:
            application.status = ApplicationStatus.SENT.value
            application.sent_at = datetime.utcnow()
            application.gmail_message_id = message_id

            logger.info(f"Application sent successfully: {application.id}")
        else:
            logger.error(f"Failed to send application: {application.id}")

        await db.flush()

        return application

    async def check_application_status(
        self,
        application: Application,
        db: AsyncSession
    ) -> Application:
        """
        Check for replies and update status.

        Args:
            application: Application instance
            db: Database session

        Returns:
            Updated application
        """
        if not application.gmail_message_id:
            return application

        status = self.gmail_client.get_message_status(application.gmail_message_id)

        if status == 'replied':
            application.status = ApplicationStatus.REPLIED.value

        application.last_status_check = datetime.utcnow()
        await db.flush()

        return application

    async def bulk_apply(
        self,
        user,
        job_ids: list[str],
        db: AsyncSession,
        limit: int = 5
    ) -> list[Application]:
        """
        Apply to multiple jobs in bulk.

        Args:
            user: User instance
            job_ids: List of job IDs to apply to
            db: Database session
            limit: Maximum number of applications to send

        Returns:
            List of created applications
        """
        applications = []

        for job_id in job_ids[:limit]:
            try:
                from sqlalchemy import select
                from app.models.job import Job

                # Fetch job
                stmt = select(Job).where(Job.id == job_id)
                result = await db.execute(stmt)
                job = result.scalar_one_or_none()

                if not job:
                    continue

                # Prepare and send
                app = await self.prepare_application(user, job, db)
                app = await self.send_application(app, db)

                applications.append(app)

            except Exception as e:
                logger.error(f"Failed to apply to job {job_id}: {str(e)}")
                continue

        logger.info(f"Bulk applied to {len(applications)} jobs")

        return applications
