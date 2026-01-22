"""Policy document ingestion pipeline orchestrator."""

import logging
from pathlib import Path
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np

from app.pipelines.policy_ingestion.pdf_processor import PDFProcessor
from app.pipelines.policy_ingestion.chunker import TextChunker
from app.models.policy_document import PolicyDocument, PolicyChunk
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import FAISSVectorStore
from app.config import settings

logger = logging.getLogger(__name__)


class PolicyIngestionOrchestrator:
    """
    Orchestrates policy document ingestion and indexing.

    Handles PDF processing, chunking, embedding generation, and storage.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: FAISSVectorStore
    ):
        """
        Initialize policy ingestion orchestrator.

        Args:
            embedding_service: Service for generating embeddings
            vector_store: FAISS vector store for chunk embeddings
        """
        self.pdf_processor = PDFProcessor()
        self.chunker = TextChunker()
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    async def ingest_document(
        self,
        file_path: str,
        metadata: dict,
        db: AsyncSession
    ) -> PolicyDocument:
        """
        Ingest a single policy document.

        Args:
            file_path: Path to PDF file
            metadata: Document metadata (title, source_url, country, document_type)
            db: Database session

        Returns:
            Created PolicyDocument object

        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If processing fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Policy document not found: {file_path}")

        logger.info(f"Starting ingestion of {file_path.name}")

        # Extract text from PDF
        full_text = self.pdf_processor.extract_text(str(file_path))

        # Create PolicyDocument record
        policy_doc = PolicyDocument(
            title=metadata.get('title', file_path.stem),
            source_url=metadata.get('source_url'),
            file_path=str(file_path),
            content_text=full_text,
            country=metadata.get('country', 'Unknown'),
            document_type=metadata.get('document_type', 'policy')
        )

        db.add(policy_doc)
        await db.flush()
        await db.refresh(policy_doc)

        logger.info(f"Created policy document record: {policy_doc.id}")

        # Process and embed chunks
        num_chunks = await self.process_and_embed(policy_doc, db)

        logger.info(f"Successfully ingested document with {num_chunks} chunks")

        return policy_doc

    async def process_and_embed(
        self,
        document: PolicyDocument,
        db: AsyncSession
    ) -> int:
        """
        Process document into chunks and generate embeddings.

        Args:
            document: PolicyDocument object
            db: Database session

        Returns:
            Number of chunks created
        """
        logger.info(f"Processing and embedding document: {document.id}")

        # Chunk the document text
        base_metadata = {
            'document_id': str(document.id),
            'document_title': document.title,
            'country': document.country,
            'document_type': document.document_type
        }

        chunks_data = self.chunker.chunk_with_metadata(
            text=document.content_text,
            base_metadata=base_metadata
        )

        # Create chunks and embeddings
        chunk_objects = []
        embeddings = []

        for chunk_data in chunks_data:
            # Generate embedding
            embedding = self.embedding_service.embed_text(chunk_data['content'])

            # Create PolicyChunk object
            chunk = PolicyChunk(
                document_id=document.id,
                chunk_index=chunk_data['metadata']['chunk_index'],
                content=chunk_data['content'],
                embedding=embedding.tobytes(),
                chunk_metadata=chunk_data['metadata']
            )

            chunk_objects.append(chunk)
            embeddings.append(embedding)

            # Add to database
            db.add(chunk)

        # Flush to get chunk IDs
        await db.flush()

        # Refresh chunks to get IDs
        for chunk in chunk_objects:
            await db.refresh(chunk)

        # Add to vector store
        if embeddings:
            embeddings_array = np.array(embeddings, dtype=np.float32)
            chunk_ids = [str(chunk.id) for chunk in chunk_objects]

            self.vector_store.add_vectors(embeddings_array, chunk_ids)

            # Save vector store
            self.vector_store.save()

        logger.info(f"Created and embedded {len(chunk_objects)} chunks")

        return len(chunk_objects)

    async def reindex_all(self, db: AsyncSession) -> int:
        """
        Rebuild vector store from all policy documents in database.

        Args:
            db: Database session

        Returns:
            Total number of chunks reindexed
        """
        logger.info("Starting full reindex of policy documents")

        # Clear existing vector store
        self.vector_store.clear()

        # Fetch all chunks
        stmt = select(PolicyChunk)
        result = await db.execute(stmt)
        all_chunks = result.scalars().all()

        if not all_chunks:
            logger.warning("No policy chunks found in database")
            return 0

        # Rebuild embeddings if needed and add to vector store
        embeddings = []
        chunk_ids = []
        chunks_without_embeddings = []

        for chunk in all_chunks:
            if chunk.embedding:
                # Use existing embedding
                embedding = np.frombuffer(chunk.embedding, dtype=np.float32)
                embeddings.append(embedding)
                chunk_ids.append(str(chunk.id))
            else:
                # Need to generate embedding
                chunks_without_embeddings.append(chunk)

        # Generate missing embeddings
        if chunks_without_embeddings:
            logger.info(f"Generating embeddings for {len(chunks_without_embeddings)} chunks")

            for chunk in chunks_without_embeddings:
                embedding = self.embedding_service.embed_text(chunk.content)
                chunk.embedding = embedding.tobytes()

                embeddings.append(embedding)
                chunk_ids.append(str(chunk.id))

            await db.flush()

        # Add all to vector store
        if embeddings:
            embeddings_array = np.array(embeddings, dtype=np.float32)
            self.vector_store.add_vectors(embeddings_array, chunk_ids)
            self.vector_store.save()

        logger.info(f"Reindexed {len(chunk_ids)} policy chunks")

        return len(chunk_ids)

    async def delete_document(
        self,
        document_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Delete a policy document and its chunks.

        Args:
            document_id: Policy document ID
            db: Database session

        Returns:
            True if deleted, False if not found
        """
        # Fetch document
        stmt = select(PolicyDocument).where(PolicyDocument.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            logger.warning(f"Document not found: {document_id}")
            return False

        # Get chunk IDs for vector store deletion
        stmt = select(PolicyChunk.id).where(PolicyChunk.document_id == document_id)
        result = await db.execute(stmt)
        chunk_ids = [str(cid) for cid in result.scalars().all()]

        # Delete from vector store
        if chunk_ids:
            self.vector_store.delete_vectors(chunk_ids)
            self.vector_store.save()

        # Delete from database (cascades to chunks)
        await db.delete(document)
        await db.flush()

        logger.info(f"Deleted document {document_id} and {len(chunk_ids)} chunks")

        return True

    async def update_document(
        self,
        document_id: str,
        file_path: str,
        db: AsyncSession
    ) -> Optional[PolicyDocument]:
        """
        Update an existing policy document with new content.

        Args:
            document_id: Existing document ID
            file_path: Path to new PDF file
            db: Database session

        Returns:
            Updated PolicyDocument or None if not found
        """
        # Fetch existing document
        stmt = select(PolicyDocument).where(PolicyDocument.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            logger.warning(f"Document not found: {document_id}")
            return None

        # Delete old chunks from vector store
        stmt = select(PolicyChunk.id).where(PolicyChunk.document_id == document_id)
        result = await db.execute(stmt)
        old_chunk_ids = [str(cid) for cid in result.scalars().all()]

        if old_chunk_ids:
            self.vector_store.delete_vectors(old_chunk_ids)

        # Delete old chunks from database
        stmt = select(PolicyChunk).where(PolicyChunk.document_id == document_id)
        result = await db.execute(stmt)
        old_chunks = result.scalars().all()
        for chunk in old_chunks:
            await db.delete(chunk)

        await db.flush()

        # Extract new text
        full_text = self.pdf_processor.extract_text(file_path)

        # Update document
        document.content_text = full_text
        document.file_path = file_path

        # Process and embed new chunks
        await self.process_and_embed(document, db)

        logger.info(f"Updated document {document_id}")

        return document
