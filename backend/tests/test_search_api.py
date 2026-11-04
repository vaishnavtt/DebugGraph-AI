"""
Integration tests for Search API endpoints (/api/v1/search/hybrid and /api/v1/search/semantic).
"""
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.retrieval.hybrid_search import HybridSearchResult, RetrievalDiagnostics

client = TestClient(app)


def test_hybrid_search_endpoint_success():
    """Verify POST /api/v1/search/hybrid returns structured results and diagnostics."""
    mock_result = HybridSearchResult(
        chunk_id="chunk_test_99",
        content="2026-11-01 ERROR [payment-service] Stripe HTTP 500 timeout",
        original_filename="payment-service.log",
        service_name="payment-service",
        severity="ERROR",
        timestamp_start="2026-11-01T10:15:00",
        timestamp_end="2026-11-01T10:15:05",
        source_line_start=14,
        source_line_end=22,
        source_entry_ids=["log_1"],
        exception_signatures=["GatewayTimeoutException"],
        dense_score=0.85,
        bm25_score=12.4,
        rrf_score=0.032,
        reranker_score=3.45,
        diagnostics=RetrievalDiagnostics(
            chunk_id="chunk_test_99",
            retrieval_methods=["dense", "bm25"],
            dense_rank=1,
            bm25_rank=1,
            dense_score=0.85,
            bm25_score=12.4,
            rrf_score=0.032,
            reranker_score=3.45,
        ),
        metadata={"custom": "val"},
    )

    with patch("app.api.search.hybrid_engine.search", return_value=[mock_result]):
        payload = {
            "query": "Why are payment transactions failing?",
            "top_k": 3,
            "service_name": "payment-service",
            "severity": "ERROR",
            "ingestion_id": None,
        }
        response = client.post("/api/v1/search/hybrid", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["query"] == "Why are payment transactions failing?"
        assert data["total_results"] == 1
        assert len(data["results"]) == 1

        hit = data["results"][0]
        assert hit["chunk_id"] == "chunk_test_99"
        assert hit["service_name"] == "payment-service"
        assert hit["severity"] == "ERROR"
        assert hit["dense_score"] == 0.85
        assert hit["bm25_score"] == 12.4
        assert hit["rrf_score"] == 0.032
        assert hit["reranker_score"] == 3.45
        assert hit["source_line_start"] == 14

        # Validate diagnostics payload
        diag = hit["diagnostics"]
        assert diag["chunk_id"] == "chunk_test_99"
        assert diag["retrieval_methods"] == ["dense", "bm25"]
        assert diag["dense_rank"] == 1
        assert diag["bm25_rank"] == 1


def test_hybrid_search_service_alias_support():
    """Verify endpoint accepts 'service' alias as 'service_name'."""
    with patch("app.api.search.hybrid_engine.search", return_value=[]) as mock_search:
        payload = {
            "query": "connection error",
            "service": "auth-service",
        }
        response = client.post("/api/v1/search/hybrid", json=payload)
        assert response.status_code == 200
        # Verify service_name was passed to search engine
        mock_search.assert_called_once()
        _, kwargs = mock_search.call_args
        assert kwargs["service_name"] == "auth-service"


def test_hybrid_search_empty_query_validation():
    """Verify validation error when query is empty."""
    response = client.post("/api/v1/search/hybrid", json={"query": ""})
    assert response.status_code == 422


def test_semantic_search_regression_protection():
    """Verify legacy /api/v1/search/semantic endpoint continues to work without disruption."""
    with patch("app.api.indexing.indexing_service.search_semantic") as mock_search:
        from app.schemas.indexing import SearchResultHit, SemanticSearchResponse

        mock_search.return_value = SemanticSearchResponse(
            query="test query",
            total_hits=1,
            hits=[
                SearchResultHit(
                    chunk_id="chunk_1",
                    similarity_score=0.91,
                    original_filename="app.log",
                    relevant_log_content="Log line content",
                    source_line_start=1,
                    source_line_end=5,
                )
            ],
        )

        response = client.post("/api/v1/search/semantic", json={"query": "test query", "top_k": 1})
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test query"
        assert data["total_hits"] == 1

