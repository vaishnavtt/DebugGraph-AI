"""
Unit and integration tests for Evaluation and Benchmarking Framework.
Verifies evaluation metrics computation, benchmark runner, and FastAPI endpoints.
"""
from fastapi.testclient import TestClient
import pytest

from app.evaluation.engine import EvaluationEngine
from app.main import app

client = TestClient(app)


def test_calculate_single_query_metrics():
    """Verify Recall@k, Precision@5, MRR, and NDCG@5 calculations."""
    engine = EvaluationEngine()
    retrieved = [
        {"content": "2026-11-04 [ERROR] ConnectionTimeoutError: timeout after 5000ms", "original_filename": "payment.log"},
        {"content": "2026-11-04 [INFO] Health probe ok", "original_filename": "gateway.log"},
        {"content": "2026-11-04 [WARN] Slow query", "original_filename": "db.log"},
        {"content": "2026-11-04 [INFO] Session created", "original_filename": "auth.log"},
        {"content": "2026-11-04 [DEBUG] Metric pushed", "original_filename": "telemetry.log"},
    ]
    gt_tokens = ["ConnectionTimeoutError", "payment gateway timed out after 5000ms"]

    m = engine.calculate_single_query_metrics(retrieved, gt_tokens, latency_ms=45.0)
    assert m["r1"] == 1.0
    assert m["r3"] == 1.0
    assert m["r5"] == 1.0
    assert m["p5"] == 0.2  # 1 hit out of 5
    assert m["mrr"] == 1.0  # hit at rank 1
    assert m["ndcg"] == 1.0


def test_evaluate_retrieval_comparisons():
    """Verify comparative metrics across Dense, BM25, Hybrid, and Reranker."""
    engine = EvaluationEngine()
    comps = engine.evaluate_retrieval(max_queries=10)
    assert len(comps) == 4

    names = [c.method for c in comps]
    assert any("Dense" in n for n in names)
    assert any("BM25" in n for n in names)
    assert any("Hybrid Fusion" in n for n in names)
    assert any("Cross-Encoder" in n for n in names)

    # Hybrid + Reranker should have highest Recall@5 and NDCG@5
    reranker_comp = next(c for c in comps if "Cross-Encoder" in c.method)
    dense_comp = next(c for c in comps if "Dense" in c.method)
    assert reranker_comp.metrics.recall_at_5 >= dense_comp.metrics.recall_at_5
    assert reranker_comp.metrics.ndcg_at_5 > dense_comp.metrics.ndcg_at_5


def test_evaluate_investigations():
    """Verify multi-agent vs single pass investigation comparison."""
    engine = EvaluationEngine()
    inv_comps = engine.evaluate_investigations()
    assert len(inv_comps) == 2

    single_pass = next(c for c in inv_comps if "Standard" in c.mode)
    multi_agent = next(c for c in inv_comps if "Multi-Agent" in c.mode)

    # Multi-agent has higher groundedness and citation precision
    assert multi_agent.metrics.evidence_groundedness > single_pass.metrics.evidence_groundedness
    assert multi_agent.metrics.citation_precision > single_pass.metrics.citation_precision


def test_api_get_evaluation_dataset():
    """Verify GET /api/v1/evaluation/dataset endpoint."""
    response = client.get("/api/v1/evaluation/dataset")
    assert response.status_code == 200
    data = response.json()
    assert data["total_retrieval_queries"] >= 30
    assert data["total_incident_scenarios"] >= 5
    assert len(data["sample_queries"]) > 0


def test_api_get_latest_evaluation():
    """Verify GET /api/v1/evaluation/latest endpoint."""
    response = client.get("/api/v1/evaluation/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"].startswith("eval_")
    assert len(data["retrieval_comparisons"]) == 4
    assert len(data["investigation_comparisons"]) == 2
    assert "Evaluation & Benchmark Report" in data["summary_markdown"]


def test_api_trigger_evaluation():
    """Verify POST /api/v1/evaluation/run endpoint."""
    response = client.post(
        "/api/v1/evaluation/run",
        json={
            "evaluate_retrieval": True,
            "evaluate_investigation": True,
            "max_queries": 5,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["run_id"].startswith("eval_")
    assert len(data["retrieval_comparisons"]) == 4


def test_api_get_overview_health():
    """Verify GET /api/v1/health/overview endpoint."""
    response = client.get("/api/v1/health/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "metrics" in data
    assert "total_ingested_logs" in data["metrics"]
    assert "total_indexed_chunks" in data["metrics"]
    assert "total_graph_services" in data["metrics"]

