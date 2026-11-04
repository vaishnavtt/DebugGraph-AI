"""
Unit tests for the EmbeddingService.
Tests dimension validation, batch embedding, query instruction formatting,
normalization, and initialization error handling.
"""
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from app.core.config import settings
from app.retrieval.embeddings import BGE_QUERY_PREFIX, EmbeddingService


def test_embedding_service_dimensions_and_batch() -> None:
    """Validate that embed_documents verifies 384 dimensions and returns float lists."""
    service = EmbeddingService(model_name="BAAI/bge-small-en-v1.5", batch_size=4)

    # Mock the underlying SentenceTransformer
    mock_model = MagicMock()
    # Mock return 2 vectors of dimension 384
    mock_embeddings = np.ones((2, 384), dtype=np.float32)
    # L2 normalize
    mock_embeddings = mock_embeddings / np.linalg.norm(mock_embeddings, axis=1, keepdims=True)
    mock_model.encode.return_value = mock_embeddings
    service._model = mock_model

    texts = ["Sample log entry 1", "Sample log entry 2"]
    vectors = service.embed_documents(texts)

    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384
    assert isinstance(vectors[0][0], float)

    mock_model.encode.assert_called_once_with(
        texts,
        batch_size=4,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )


def test_embed_query_applies_bge_prefix() -> None:
    """Ensure query embedding applies the recommended BGE instruction prefix."""
    service = EmbeddingService()
    mock_model = MagicMock()
    mock_vec = np.ones((384,), dtype=np.float32)
    mock_vec = mock_vec / np.linalg.norm(mock_vec)
    mock_model.encode.return_value = mock_vec
    service._model = mock_model

    query = "database connection timeout"
    vec = service.embed_query(query)

    assert len(vec) == 384
    expected_call_text = f"{BGE_QUERY_PREFIX}{query}"
    mock_model.encode.assert_called_once_with(
        expected_call_text,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )


def test_embed_query_empty_fails() -> None:
    """Ensure empty or whitespace-only queries raise ValueError."""
    service = EmbeddingService()
    with pytest.raises(ValueError, match="cannot be empty"):
        service.embed_query("   ")


def test_dimension_mismatch_raises_error() -> None:
    """Ensure invalid vector dimensionality raises ValueError."""
    service = EmbeddingService()
    mock_model = MagicMock()
    # Return incorrect dimension (e.g., 512 instead of 384)
    mock_model.encode.return_value = np.zeros((1, 512), dtype=np.float32)
    service._model = mock_model

    with pytest.raises(ValueError, match="dimension mismatch"):
        service.embed_documents(["Test text"])


def test_model_initialization_failure() -> None:
    """Ensure model loading errors are caught and re-raised with descriptive RuntimeError."""
    service = EmbeddingService(model_name="nonexistent/fake-model-1234")
    with patch("app.retrieval.embeddings.SentenceTransformer", side_effect=Exception("Model not found")):
        with pytest.raises(RuntimeError, match="Could not initialize embedding model"):
            service.embed_documents(["Test"])

