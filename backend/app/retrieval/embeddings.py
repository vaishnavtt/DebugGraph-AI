"""
Embedding Service for DebugGraph AI.
Generates normalized dense vector embeddings using Sentence Transformers (BAAI/bge-small-en-v1.5).
"""
from typing import List, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover
    SentenceTransformer = None  # type: ignore[assignment, misc]

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# BGE instruction recommendation for asymmetric query retrieval
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class EmbeddingService:
    """Singleton-style wrapper managing SentenceTransformer model lifecycle."""

    _instance: Optional["EmbeddingService"] = None
    _model = None

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        batch_size: Optional[int] = None,
    ) -> None:
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.device = device or settings.EMBEDDING_DEVICE
        self.batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        self.expected_dim = settings.VECTOR_SIZE

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        """Retrieve or construct the singleton EmbeddingService instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_model(self):
        """Lazy load the underlying SentenceTransformer model."""
        if self._model is None:
            logger.info(
                "Loading embedding model '%s' on device '%s'...",
                self.model_name,
                self.device,
            )
            try:
                if SentenceTransformer is None:
                    raise RuntimeError("sentence-transformers package is required.")

                self._model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                )
                logger.info("Embedding model loaded successfully.")
            except Exception as exc:
                logger.error("Failed to initialize embedding model '%s': %s", self.model_name, exc)
                raise RuntimeError(
                    f"Could not initialize embedding model '{self.model_name}' on device '{self.device}': {exc}"
                ) from exc
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate normalized embeddings for document chunks.
        Documents are encoded without the query instruction prefix.
        """
        if not texts:
            return []

        model = self._load_model()
        try:
            embeddings = model.encode(
                texts,
                batch_size=self.batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
        except Exception as exc:
            logger.error("Error during document batch embedding: %s", exc)
            raise RuntimeError(f"Embedding generation failed: {exc}") from exc

        # Validate dimensionality
        if len(embeddings.shape) != 2 or embeddings.shape[1] != self.expected_dim:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.expected_dim}, got {embeddings.shape[1]}"
            )

        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """
        Generate a normalized embedding for a search query.
        Applies BGE query instruction prefix for enhanced retrieval accuracy.
        """
        if not query or not query.strip():
            raise ValueError("Query string cannot be empty.")

        model = self._load_model()
        formatted_query = f"{BGE_QUERY_PREFIX}{query.strip()}"

        try:
            vector = model.encode(
                formatted_query,
                normalize_embeddings=True,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
        except Exception as exc:
            logger.error("Error during query embedding: %s", exc)
            raise RuntimeError(f"Query embedding generation failed: {exc}") from exc

        if vector.shape[0] != self.expected_dim:
            raise ValueError(
                f"Query embedding dimension mismatch: expected {self.expected_dim}, got {vector.shape[0]}"
            )

        return vector.tolist()

