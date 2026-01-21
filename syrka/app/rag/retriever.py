"""Policy document retrieval system."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import logging

from app.models.policy_document import PolicyChunk, PolicyDocument
from app.rag.vector_store import FAISSVectorStore
from app.rag.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class PolicyRetriever:
    """
    Retriever for policy documents using vector similarity search.

    Combines FAISS vector search with database filtering for efficient
    and flexible retrieval of relevant policy content.
    """

    def __init__(
        self,
        vector_store: FAISSVectorStore,
        embedding_service: EmbeddingService
    ):
        """
        Initialize policy retriever.

        Args:
            vector_store: FAISS vector store containing policy chunk embeddings
            embedding_service: Service for generating query embeddings
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    async def retrieve(
        self,
        query: str,
        db: AsyncSession,
        k: int = 5,
        filters: Optional[dict] = None
    ) -> list[PolicyChunk]:
        """
        Retrieve relevant policy chunks for a query.

        Args:
            query: Search query text
            db: Database session
            k: Number of chunks to retrieve
            filters: Optional filters (sector, country, document_type)

        Returns:
            List of PolicyChunk objects ordered by relevance
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)

        # Search vector store
        results = self.vector_store.search(query_embedding, k=k * 2)  # Get extra for filtering

        if not results:
            return []

        # Extract chunk IDs
        chunk_ids = [chunk_id for chunk_id, _ in results]

        # Fetch chunks from database
        stmt = select(PolicyChunk).where(PolicyChunk.id.in_(chunk_ids))

        # Apply filters if provided
        if filters:
            # Join with policy documents to filter
            stmt = stmt.join(PolicyDocument)

            if 'sector' in filters and filters['sector']:
                # Filter by metadata (assuming sector is stored in chunk metadata)
                # This would need adjustment based on actual metadata structure
                pass

            if 'country' in filters and filters['country']:
                stmt = stmt.where(PolicyDocument.country == filters['country'])

            if 'document_type' in filters and filters['document_type']:
                stmt = stmt.where(PolicyDocument.document_type == filters['document_type'])

        result = await db.execute(stmt)
        chunks = result.scalars().all()

        # Order chunks by similarity scores from vector search
        chunk_order = {chunk_id: idx for idx, (chunk_id, _) in enumerate(results)}
        chunks_sorted = sorted(
            chunks,
            key=lambda c: chunk_order.get(str(c.id), float('inf'))
        )

        # Return top k
        return chunks_sorted[:k]

    async def retrieve_by_sector(
        self,
        sector: str,
        db: AsyncSession,
        k: int = 5
    ) -> list[PolicyChunk]:
        """
        Retrieve policy chunks relevant to a specific sector.

        Args:
            sector: Target sector
            db: Database session
            k: Number of chunks to retrieve

        Returns:
            List of PolicyChunk objects
        """
        query = f"National priorities and policies for {sector} sector"
        return await self.retrieve(
            query=query,
            db=db,
            k=k,
            filters={'sector': sector}
        )

    async def retrieve_by_skills(
        self,
        skills: list[str],
        db: AsyncSession,
        k: int = 5
    ) -> list[PolicyChunk]:
        """
        Retrieve policy chunks mentioning specific skills.

        Args:
            skills: List of skills to search for
            db: Database session
            k: Number of chunks to retrieve

        Returns:
            List of PolicyChunk objects
        """
        query = f"Policies and priorities related to skills: {', '.join(skills)}"
        return await self.retrieve(query=query, db=db, k=k)

    async def retrieve_by_document(
        self,
        document_id: str,
        db: AsyncSession,
        query: str,
        k: int = 5
    ) -> list[PolicyChunk]:
        """
        Retrieve chunks from a specific document.

        Args:
            document_id: Policy document ID
            db: Database session
            query: Search query
            k: Number of chunks to retrieve

        Returns:
            List of PolicyChunk objects from the specified document
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)

        # Get all chunks from this document
        stmt = select(PolicyChunk).where(PolicyChunk.document_id == document_id)
        result = await db.execute(stmt)
        chunks = result.scalars().all()

        if not chunks:
            return []

        # Calculate similarities
        chunk_similarities = []
        for chunk in chunks:
            if chunk.embedding:
                import numpy as np
                chunk_embedding = np.frombuffer(chunk.embedding, dtype=np.float32)
                similarity = self.embedding_service.similarity(
                    query_embedding,
                    chunk_embedding
                )
                chunk_similarities.append((chunk, similarity))

        # Sort by similarity
        chunk_similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top k
        return [chunk for chunk, _ in chunk_similarities[:k]]
