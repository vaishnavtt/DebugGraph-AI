"""
Unit tests for Cross-Encoder Reranker.
Uses deterministic mocks to test logic without downloading heavy model weights.
"""
from unittest.mock import MagicMock
import pytest

from app.retrieval.reranker import CrossEncoderReranker


def test_reranker_empty_candidates():
    """Ensure empty candidate list returns empty without attempting inference."""
    reranker = CrossEncoderReranker()
    assert reranker.rerank(query="anything", candidates=[]) == []


def test_reranker_empty_query():
    """Ensure empty query returns candidates in original order without error."""
    reranker = CrossEncoderReranker()
    candidates = [
        {"chunk_id": "c1", "content": "chunk 1", "rrf_score": 0.05},
        {"chunk_id": "c2", "content": "chunk 2", "rrf_score": 0.04},
    ]
    reranked = reranker.rerank(query="   ", candidates=candidates)
    assert len(reranked) == 2
    assert reranked[0]["chunk_id"] == "c1"
    assert reranked[1]["chunk_id"] == "c2"


def test_reranker_reordering_with_mock():
    """Verify cross-encoder reorders candidates based on relevance score."""
    mock_model = MagicMock()
    # Mock predict returns logits: lower score for c1, higher score for c2
    mock_model.predict.return_value = [-1.5, 3.8]

    reranker = CrossEncoderReranker(model=mock_model)
    candidates = [
        {"chunk_id": "c1", "content": "Irrelevant general info", "original_filename": "app.log"},
        {"chunk_id": "c2", "content": "Target critical failure in DB", "original_filename": "app.log"},
    ]

    reranked = reranker.rerank(query="database failure", candidates=candidates)

    # c2 had score 3.8 so it should be ranked first
    assert len(reranked) == 2
    assert reranked[0]["chunk_id"] == "c2"
    assert reranked[0]["reranker_score"] == 3.8
    assert reranked[0]["original_filename"] == "app.log"

    assert reranked[1]["chunk_id"] == "c1"
    assert reranked[1]["reranker_score"] == -1.5


def test_reranker_graceful_inference_failure():
    """Verify reranker handles inference exceptions without crashing and preserves original order."""
    mock_model = MagicMock()
    mock_model.predict.side_effect = RuntimeError("CUDA out of memory simulation")

    reranker = CrossEncoderReranker(model=mock_model)
    candidates = [
        {"chunk_id": "c1", "content": "Chunk 1", "rrf_score": 0.03},
        {"chunk_id": "c2", "content": "Chunk 2", "rrf_score": 0.02},
    ]

    # Should not raise exception
    reranked = reranker.rerank(query="timeout error", candidates=candidates)
    assert len(reranked) == 2
    assert reranked[0]["chunk_id"] == "c1"
    assert reranked[0]["reranker_score"] is None
    assert reranked[1]["chunk_id"] == "c2"

