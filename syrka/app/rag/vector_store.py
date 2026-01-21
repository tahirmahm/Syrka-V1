"""FAISS vector store for similarity search."""

import faiss
import numpy as np
import pickle
import logging
from pathlib import Path
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """
    FAISS-based vector store for efficient similarity search.

    Supports adding, searching, and persisting vector embeddings with associated IDs.
    """

    def __init__(self, dimension: int = None, index_path: str = None):
        """
        Initialize FAISS vector store.

        Args:
            dimension: Embedding dimension (defaults to config setting)
            index_path: Path to load existing index from
        """
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self.index_path = index_path or settings.FAISS_INDEX_PATH

        # Initialize FAISS index (using L2 distance, will normalize for cosine similarity)
        self.index = faiss.IndexFlatL2(self.dimension)

        # Map index positions to IDs
        self.id_map: list[str] = []

        # Try to load existing index
        if index_path and Path(index_path).exists():
            self.load(index_path)

    def add_vectors(self, vectors: np.ndarray, ids: list[str]) -> None:
        """
        Add vectors to the index.

        Args:
            vectors: 2D numpy array of vectors (n_vectors x dimension)
            ids: List of string IDs corresponding to vectors
        """
        if len(vectors) != len(ids):
            raise ValueError("Number of vectors must match number of IDs")

        if len(vectors) == 0:
            return

        # Normalize vectors for cosine similarity
        vectors = vectors.astype(np.float32)
        faiss.normalize_L2(vectors)

        # Add to index
        self.index.add(vectors)

        # Update ID mapping
        self.id_map.extend(ids)

        logger.info(f"Added {len(vectors)} vectors to index. Total: {len(self.id_map)}")

    def search(self, query_vector: np.ndarray, k: int = 10) -> list[tuple[str, float]]:
        """
        Search for k nearest neighbors to query vector.

        Args:
            query_vector: Query embedding vector
            k: Number of results to return

        Returns:
            List of (id, similarity_score) tuples, sorted by similarity (highest first)
        """
        if len(self.id_map) == 0:
            return []

        # Normalize query vector
        query_vector = query_vector.astype(np.float32).reshape(1, -1)
        faiss.normalize_L2(query_vector)

        # Limit k to available vectors
        k = min(k, len(self.id_map))

        # Search
        distances, indices = self.index.search(query_vector, k)

        # Convert L2 distances to similarity scores (0 to 1)
        # Since vectors are normalized, L2 distance relates to cosine similarity:
        # similarity = 1 - (distance^2 / 2)
        similarities = 1 - (distances[0] / 2)
        similarities = np.clip(similarities, 0, 1)

        # Build result list
        results = []
        for idx, similarity in zip(indices[0], similarities):
            if idx < len(self.id_map):  # Safety check
                results.append((self.id_map[idx], float(similarity)))

        return results

    def delete_vectors(self, ids: list[str]) -> None:
        """
        Delete vectors by ID.

        Note: This rebuilds the index, which can be expensive for large indexes.

        Args:
            ids: List of IDs to delete
        """
        ids_to_delete = set(ids)

        # Find indices to keep
        keep_indices = [
            i for i, vid in enumerate(self.id_map)
            if vid not in ids_to_delete
        ]

        if len(keep_indices) == len(self.id_map):
            return  # Nothing to delete

        # Extract vectors to keep
        vectors_to_keep = []
        new_id_map = []

        for idx in keep_indices:
            # Reconstruct vector from index
            vector = self.index.reconstruct(idx)
            vectors_to_keep.append(vector)
            new_id_map.append(self.id_map[idx])

        # Rebuild index
        self.index = faiss.IndexFlatL2(self.dimension)
        self.id_map = []

        if vectors_to_keep:
            vectors_array = np.array(vectors_to_keep, dtype=np.float32)
            self.add_vectors(vectors_array, new_id_map)

        logger.info(f"Deleted {len(ids_to_delete)} vectors from index")

    def save(self, path: str = None) -> None:
        """
        Save index and ID mapping to disk.

        Args:
            path: Directory path to save to (defaults to configured path)
        """
        save_path = Path(path or self.index_path)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        index_file = save_path / "index.faiss"
        faiss.write_index(self.index, str(index_file))

        # Save ID mapping
        id_map_file = save_path / "id_map.pkl"
        with open(id_map_file, 'wb') as f:
            pickle.dump(self.id_map, f)

        logger.info(f"Saved vector store to {save_path}")

    def load(self, path: str = None) -> None:
        """
        Load index and ID mapping from disk.

        Args:
            path: Directory path to load from (defaults to configured path)
        """
        load_path = Path(path or self.index_path)

        if not load_path.exists():
            logger.warning(f"Index path {load_path} does not exist")
            return

        # Load FAISS index
        index_file = load_path / "index.faiss"
        if index_file.exists():
            self.index = faiss.read_index(str(index_file))
            logger.info(f"Loaded FAISS index from {index_file}")

        # Load ID mapping
        id_map_file = load_path / "id_map.pkl"
        if id_map_file.exists():
            with open(id_map_file, 'rb') as f:
                self.id_map = pickle.load(f)
            logger.info(f"Loaded ID map with {len(self.id_map)} entries")

    def clear(self) -> None:
        """Clear all vectors from the index."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.id_map = []
        logger.info("Cleared vector store")

    def size(self) -> int:
        """
        Get number of vectors in the index.

        Returns:
            Number of vectors
        """
        return len(self.id_map)
