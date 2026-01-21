"""Embedding generation service for RAG and matching."""

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Union, Optional
import logging
import openai

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using HuggingFace or OpenAI.

    Uses sentence-transformers by default, with OpenAI as fallback.
    """

    def __init__(self, model_name: str = None):
        """
        Initialize embedding service.

        Args:
            model_name: HuggingFace model name (defaults to config setting)
        """
        self.model_name = model_name or settings.HF_MODEL_NAME
        self.dimension = settings.EMBEDDING_DIMENSION
        self.model: Optional[SentenceTransformer] = None
        self._load_model()

    def _load_model(self) -> None:
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(
                self.model_name,
                cache_folder=settings.HF_CACHE_DIR
            )
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            self.model = None

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            Numpy array containing the embedding vector

        Raises:
            Exception: If embedding generation fails
        """
        if not text or not text.strip():
            return np.zeros(self.dimension, dtype=np.float32)

        try:
            if self.model is not None:
                embedding = self.model.encode(text, convert_to_numpy=True)
                return embedding.astype(np.float32)
            else:
                # Fallback to OpenAI
                return self.embed_with_openai(text)
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            # Return zero vector as fallback
            return np.zeros(self.dimension, dtype=np.float32)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to embed

        Returns:
            2D numpy array where each row is an embedding vector
        """
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)

        try:
            if self.model is not None:
                embeddings = self.model.encode(
                    texts,
                    convert_to_numpy=True,
                    show_progress_bar=len(texts) > 100
                )
                return embeddings.astype(np.float32)
            else:
                # Fallback: embed one by one with OpenAI
                embeddings = [self.embed_with_openai(text) for text in texts]
                return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
            return np.zeros((len(texts), self.dimension), dtype=np.float32)

    def embed_with_openai(self, text: str) -> np.ndarray:
        """
        Generate embedding using OpenAI API as fallback.

        Args:
            text: Input text to embed

        Returns:
            Numpy array containing the embedding vector
        """
        try:
            openai.api_key = settings.OPENAI_API_KEY
            response = openai.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=text
            )
            embedding = np.array(response.data[0].embedding, dtype=np.float32)

            # If dimensions don't match, we need to resize (pad or truncate)
            if len(embedding) != self.dimension:
                logger.warning(
                    f"OpenAI embedding dimension ({len(embedding)}) "
                    f"doesn't match expected ({self.dimension})"
                )
                if len(embedding) > self.dimension:
                    embedding = embedding[:self.dimension]
                else:
                    embedding = np.pad(
                        embedding,
                        (0, self.dimension - len(embedding)),
                        mode='constant'
                    )

            return embedding
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {str(e)}")
            return np.zeros(self.dimension, dtype=np.float32)

    def similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embedding vectors.

        Args:
            vec1: First embedding vector
            vec2: Second embedding vector

        Returns:
            Cosine similarity score (0 to 1)
        """
        if vec1 is None or vec2 is None:
            return 0.0

        # Normalize vectors
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
        vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)

        # Compute cosine similarity
        similarity = np.dot(vec1_norm, vec2_norm)

        # Ensure result is between 0 and 1
        return float(max(0.0, min(1.0, similarity)))
