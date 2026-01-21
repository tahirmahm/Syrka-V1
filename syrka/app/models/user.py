"""User model for authentication and profile management."""

from sqlalchemy import Column, String, Integer, DateTime, Enum, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    USER = "user"
    EDUCATOR = "educator"
    GOVERNMENT = "government"


class User(Base):
    """
    User model representing job seekers, educators, and government users.

    Attributes:
        id: Unique identifier (UUID)
        email: User's email address (unique)
        hashed_password: Bcrypt hashed password
        full_name: User's full name
        role: User role (user/educator/government)
        skills: JSON array of user's skills
        experience_years: Years of professional experience
        location: User's location/region
        sector_preference: Preferred industry sector
        resume_text: Full text of user's resume
        created_at: Account creation timestamp
        updated_at: Last profile update timestamp
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False, index=True)

    # Profile information
    skills = Column(JSON, default=list, nullable=False)
    experience_years = Column(Integer, default=0)
    location = Column(String(255))
    sector_preference = Column(String(100), index=True)
    resume_text = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
