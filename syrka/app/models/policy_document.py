"""Policy document and chunk models for RAG system."""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, JSON, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class PolicyDocument(Base):
    """
    Government policy document model for RAG ingestion.

    Attributes:
        id: Unique identifier (UUID)
        title: Document title
        source_url: Original URL or reference
        file_path: Path to stored file
        content_text: Full extracted text
        processed_at: When document was processed
        country: Country of origin
        document_type: Type of policy document
    """

    __tablename__ = "policy_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(500), nullable=False, index=True)
    source_url = Column(Text)
    file_path = Column(String(500), nullable=False)
    content_text = Column(Text, nullable=False)
    processed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    country = Column(String(100), index=True)
    document_type = Column(String(100), index=True)  # national_plan, sector_strategy, education_policy, etc.

    def __repr__(self) -> str:
        return f"<PolicyDocument(id={self.id}, title='{self.title}')>"


class PolicyChunk(Base):
    """
    Chunked policy document text for vector retrieval.

    Attributes:
        id: Unique identifier (UUID)
        document_id: Foreign key to PolicyDocument
        chunk_index: Sequential index within document
        content: Chunk text content
        embedding: Vector embedding for similarity search
        metadata: Additional JSON metadata (section, page, etc.)
    """

    __tablename__ = "policy_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("policy_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(LargeBinary)  # Vector embedding stored as bytes
    metadata = Column(JSON, default=dict, nullable=False)  # {"section": "...", "page": 5, etc.}

    # Relationship
    document = relationship("PolicyDocument", backref="chunks")

    def __repr__(self) -> str:
        return f"<PolicyChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"
