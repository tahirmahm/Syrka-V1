"""Application tracking model for job application automation."""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database import Base


class ApplicationStatus(str, enum.Enum):
    """Application status enumeration."""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    REPLIED = "replied"
    REJECTED = "rejected"
    ACCEPTED = "accepted"


class Application(Base):
    """
    Job application model tracking automated applications.

    Attributes:
        id: Unique identifier (UUID)
        user_id: Foreign key to User
        job_id: Foreign key to Job
        status: Current application status
        tailored_cv: AI-generated tailored CV text
        cover_letter: AI-generated cover letter
        sent_at: Timestamp when application was sent
        gmail_message_id: Gmail API message ID for tracking
        last_status_check: Last time we checked for replies
        created_at: When application was created
    """

    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    # Application status and tracking
    status = Column(String(50), default=ApplicationStatus.DRAFT.value, nullable=False, index=True)

    # Generated content
    tailored_cv = Column(Text)
    cover_letter = Column(Text)

    # Email tracking
    sent_at = Column(DateTime(timezone=True))
    gmail_message_id = Column(String(255), unique=True)
    last_status_check = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Application(id={self.id}, user_id={self.user_id}, job_id={self.job_id}, status='{self.status}')>"
