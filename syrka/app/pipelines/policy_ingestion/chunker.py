"""Text chunking for policy documents."""

import re
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Text chunker for splitting policy documents into manageable chunks.

    Implements various chunking strategies for optimal retrieval performance.
    """

    def __init__(
        self,
        chunk_size: int = None,
        overlap: int = None
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size: Target size of each chunk in characters
            overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self.overlap = overlap or settings.RAG_CHUNK_OVERLAP

    def chunk_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None
    ) -> list[str]:
        """
        Split text into overlapping chunks of approximately equal size.

        Args:
            text: Text to chunk
            chunk_size: Override default chunk size
            overlap: Override default overlap

        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.overlap

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # Find end position
            end = start + chunk_size

            # If not at the end, try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                search_start = max(start, end - 100)  # Look back up to 100 chars
                search_text = text[search_start:end + 100]

                # Find last sentence ending
                sentence_end_match = None
                for match in re.finditer(r'[.!?]\s+', search_text):
                    sentence_end_match = match

                if sentence_end_match:
                    # Adjust end to sentence boundary
                    end = search_start + sentence_end_match.end()

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - overlap

        logger.debug(f"Split text into {len(chunks)} chunks (avg size: {sum(len(c) for c in chunks) // len(chunks)})")

        return chunks

    def chunk_by_sections(self, structured_text: dict) -> list[dict]:
        """
        Chunk text preserving section structure from PDF.

        Args:
            structured_text: Structured text from PDFProcessor.extract_with_structure()

        Returns:
            List of chunk dictionaries with metadata:
            [
                {
                    'content': '...',
                    'metadata': {
                        'page': 1,
                        'section': 'Introduction',
                        'chunk_index': 0
                    }
                },
                ...
            ]
        """
        chunks = []
        chunk_index = 0

        pages = structured_text.get('pages', [])

        for page in pages:
            page_num = page.get('page_num', 0)
            text = page.get('text', '')
            headings = page.get('headings', [])

            # If page has headings, split by sections
            if headings and len(text) > self.chunk_size:
                # Split text by heading positions (simplified approach)
                # In production, would need more sophisticated section detection
                text_chunks = self.chunk_text(text)

                for i, chunk in enumerate(text_chunks):
                    # Try to associate with nearest heading
                    section = headings[0]['text'] if headings else 'Content'

                    chunks.append({
                        'content': chunk,
                        'metadata': {
                            'page': page_num,
                            'section': section,
                            'chunk_index': chunk_index
                        }
                    })
                    chunk_index += 1
            else:
                # Small page, keep as single chunk
                if text.strip():
                    chunks.append({
                        'content': text,
                        'metadata': {
                            'page': page_num,
                            'section': headings[0]['text'] if headings else 'Content',
                            'chunk_index': chunk_index
                        }
                    })
                    chunk_index += 1

        logger.info(f"Created {len(chunks)} section-aware chunks")

        return chunks

    def smart_chunk(self, text: str) -> list[str]:
        """
        Intelligent chunking that respects sentence and paragraph boundaries.

        Args:
            text: Text to chunk

        Returns:
            List of chunks
        """
        # Split into paragraphs first
        paragraphs = re.split(r'\n\s*\n', text)

        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(paragraph) > self.chunk_size:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # If paragraph itself is too large, split it
                if len(paragraph) > self.chunk_size:
                    para_chunks = self.chunk_text(paragraph)
                    chunks.extend(para_chunks[:-1])
                    current_chunk = para_chunks[-1] if para_chunks else ""
                else:
                    current_chunk = paragraph
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        logger.debug(f"Smart chunked text into {len(chunks)} chunks")

        return chunks

    def chunk_with_metadata(
        self,
        text: str,
        base_metadata: dict
    ) -> list[dict]:
        """
        Chunk text and attach metadata to each chunk.

        Args:
            text: Text to chunk
            base_metadata: Base metadata to attach to all chunks

        Returns:
            List of chunk dictionaries with content and metadata
        """
        text_chunks = self.smart_chunk(text)

        chunks_with_metadata = []
        for idx, chunk in enumerate(text_chunks):
            chunk_data = {
                'content': chunk,
                'metadata': {
                    **base_metadata,
                    'chunk_index': idx,
                    'total_chunks': len(text_chunks)
                }
            }
            chunks_with_metadata.append(chunk_data)

        return chunks_with_metadata

    def merge_small_chunks(
        self,
        chunks: list[str],
        min_size: int = 100
    ) -> list[str]:
        """
        Merge chunks that are smaller than minimum size.

        Args:
            chunks: List of chunks
            min_size: Minimum chunk size in characters

        Returns:
            List of merged chunks
        """
        if not chunks:
            return []

        merged = []
        current = chunks[0]

        for chunk in chunks[1:]:
            if len(current) < min_size:
                current += " " + chunk
            else:
                merged.append(current)
                current = chunk

        # Add last chunk
        merged.append(current)

        logger.debug(f"Merged {len(chunks)} chunks into {len(merged)} chunks")

        return merged
