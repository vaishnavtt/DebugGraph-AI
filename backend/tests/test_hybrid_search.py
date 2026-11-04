"""
Unit and integration tests for Hybrid Retrieval Orchestrator.
"""
from unittest.mock import MagicMock
import pytest

from app.retrieval.hybrid_search import HybridSearchEngine


def test_hybrid_search_end_to_end_pipeline():
    """Verify dense + sparse retrieval, RRF fusion, cross-encoder reranking, and diagnostics."""
    mock_vector_store = MagicMock()
    mock_bm25_service = MagicMock()
    mock_embedding_service = MagicMock()
    mock_reranker = MagicMock()

    # Embedding mock
    mock_embedding_service.embed_query.return_value = [0.1] * 384

    # Dense results: c_dense and c_both
    mock_vector_store.search.return_value = [
        {
            "chunk_id": "c_dense",
            "similarity_score": 0.88,
            "content": "Dense content only",
            "original_filename": "service.log",
            "service_name": "payment-service",
            "severity": "ERROR",
            "source_line_start": 10,
            "source_line_end": 15,
        },
        {
            "chunk_id": "c_both",
            "similarity_score": 0.82,
            "content": "Content found by both",
            "original_filename": "service.log",
            "service_name": "payment-service",
            "severity": "ERROR",
            "source_line_start": 20,
            "source_line_end": 25,
        },
    ]

    # BM25 results: c_sparse and c_both
    mock_bm25_service.search.return_value = [
        {
            "chunk_id": "c_both",
            "bm25_score": 15.0,
            "content": "Content found by both",
            "original_filename": "service.log",
            "service_name": "payment-service",
            "severity": "ERROR",
            "source_line_start": 20,
            "source_line_end": 25,
        },
        {
            "chunk_id": "c_sparse",
            "bm25_score": 11.2,
            "content": "Sparse content only",
            "original_filename": "service.log",
            "service_name": "payment-service",
            "severity": "WARNING",
            "source_line_start": 30,
            "source_line_end": 35,
        },
    ]

    # Reranker mock: prioritize c_both
    mock_reranker.rerank.side_effect = lambda query, candidates, top_k: [
        {**c.to_dict(), "reranker_score": 4.5} if c.chunk_id == "c_both" else {**c.to_dict(), "reranker_score": 1.2}
        for c in sorted(candidates, key=lambda x: 4.5 if x.chunk_id == "c_both" else 1.2, reverse=True)[:top_k]
    ]

    engine = HybridSearchEngine(
        vector_store=mock_vector_store,
        embedding_service=mock_embedding_service,
        bm25_service=mock_bm25_service,
        reranker=mock_reranker,
    )

    results = engine.search(
        query="payment gateway failure",
        top_k=2,
        service_name="payment-service",
        severity="ERROR",
    )

    assert len(results) == 2

    top = results[0]
    assert top.chunk_id == "c_both"
    assert top.reranker_score == 4.5
    assert "dense" in top.diagnostics.retrieval_methods
    assert "bm25" in top.diagnostics.retrieval_methods
    assert top.diagnostics.dense_rank == 2
    assert top.diagnostics.bm25_rank == 1
    assert top.dense_score == 0.82
    assert top.bm25_score == 15.0
    assert top.diagnostics.rrf_score > 0
    assert top.source_line_start == 20


def test_hybrid_search_fallback_when_dense_fails():
    """Verify hybrid search gracefully proceeds with BM25 if dense search throws an error."""
    mock_vector_store = MagicMock()
    mock_vector_store.search.side_effect = ConnectionError("Qdrant unavailable")

    mock_bm25_service = MagicMock()
    mock_bm25_service.search.return_value = [
        {
            "chunk_id": "c_sparse_only",
            "bm25_score": 10.0,
            "content": "BM25 content",
            "original_filename": "app.log",
            "source_line_start": 1,
            "source_line_end": 4,
        }
    ]

    mock_reranker = MagicMock()
    mock_reranker.rerank.side_effect = lambda query, candidates, top_k: [
        {**c.to_dict(), "reranker_score": 2.0} for c in candidates[:top_k]
    ]

    engine = HybridSearchEngine(
        vector_store=mock_vector_store,
        bm25_service=mock_bm25_service,
        reranker=mock_reranker,
    )

    results = engine.search(query="error code", top_k=5)
    assert len(results) == 1
    assert results[0].chunk_id == "c_sparse_only"
    assert results[0].diagnostics.retrieval_methods == ["bm25"]
    assert results[0].diagnostics.dense_rank is None

