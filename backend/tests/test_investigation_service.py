"""
Unit and integration tests for IncidentInvestigationService.
Tests retrieval integration, evidence grounding, empty retrieval handling,
hallucination filtering, and exception propagation.
All external LLM calls are mocked.
"""
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.core.errors import GeminiAPIError, GeminiInvalidResponseError
from app.retrieval.hybrid_search import HybridSearchResult, RetrievalDiagnostics
from app.schemas.investigation import InvestigationRequest
from app.services.incident_investigation_service import IncidentInvestigationService


def create_mock_search_result(
    chunk_id: str,
    content: str,
    filename: str = "payment.log",
    service: str = "payment-service",
    severity: str = "ERROR",
    line_start: int = 10,
    line_end: int = 25,
) -> HybridSearchResult:
    """Helper creating a fully populated HybridSearchResult instance."""
    diagnostics = RetrievalDiagnostics(
        chunk_id=chunk_id,
        retrieval_methods=["dense", "bm25"],
        dense_rank=1,
        bm25_rank=1,
        dense_score=0.92,
        bm25_score=14.5,
        rrf_score=0.032,
        reranker_score=4.12,
    )
    return HybridSearchResult(
        chunk_id=chunk_id,
        content=content,
        original_filename=filename,
        service_name=service,
        severity=severity,
        timestamp_start="2026-11-01T10:00:00Z",
        timestamp_end="2026-11-01T10:05:00Z",
        source_line_start=line_start,
        source_line_end=line_end,
        source_entry_ids=[f"{chunk_id}_entry_1"],
        exception_signatures=["ConnectionTimeoutError"],
        dense_score=0.92,
        bm25_score=14.5,
        rrf_score=0.032,
        reranker_score=4.12,
        diagnostics=diagnostics,
    )


@pytest.mark.asyncio
async def test_investigate_successful_pipeline():
    """Verify full investigation pipeline with hybrid retrieval and Gemini output parsing."""
    mock_hybrid = MagicMock()
    chunk1 = create_mock_search_result("chunk_payment_1", "ConnectionTimeoutError contacting Stripe API")
    chunk2 = create_mock_search_result("chunk_payment_2", "HTTP 500 downstream payment gateway timed out")
    mock_hybrid.search.return_value = [chunk1, chunk2]

    mock_gemini = MagicMock()
    mock_gemini.model_name = "gemini-flash-latest"
    mock_gemini.generate_json = AsyncMock(
        return_value={
            "data": {
                "incident_summary": "The payment service experienced recurring timeouts contacting the upstream gateway.",
                "affected_services": ["payment-service"],
                "severity_assessment": "HIGH",
                "key_observations": [
                    {
                        "observation": "ConnectionTimeoutError raised when contacting payment gateway.",
                        "category": "EXCEPTION",
                        "is_fact": True,
                        "timestamp": "2026-11-01T10:00:00Z",
                        "affected_service": "payment-service",
                        "evidence_chunk_ids": ["chunk_payment_1"],
                    }
                ],
                "potential_root_causes": [
                    {
                        "rank": 1,
                        "hypothesis": "External payment gateway latency or network partition.",
                        "reasoning": "Consistent 30s timeout observed in outgoing HTTP calls.",
                        "confidence": "HIGH",
                        "confidence_reasoning": "Direct stack traces corroborate connection timeouts.",
                        "supporting_evidence_ids": ["chunk_payment_1", "chunk_payment_2"],
                    }
                ],
                "supporting_evidence": [
                    {
                        "chunk_id": "chunk_payment_1",
                        "relevant_excerpt": "ConnectionTimeoutError contacting Stripe API",
                        "relevance_explanation": "Direct indicator of outbound connection degradation.",
                    }
                ],
                "recommended_actions": [
                    {
                        "priority": 1,
                        "action": "Inspect egress network routing and gateway status page",
                        "category": "IMMEDIATE_MITIGATION",
                        "rationale": "Determine if issue is external or internal proxy misconfiguration.",
                    }
                ],
                "further_investigation": {
                    "missing_evidence": ["Stripe API external latency metrics", "Egress NAT gateway logs"],
                    "recommended_checks": ["curl -Iv https://api.stripe.com/healthcheck"],
                },
                "evidence_sufficiency": {
                    "status": "SUFFICIENT",
                    "reason": "Detailed stack traces and error logs correlate across both chunks.",
                    "confidence_score": 0.9,
                },
            },
            "prompt_tokens": 400,
            "completion_tokens": 250,
            "total_tokens": 650,
            "latency_ms": 320.5,
            "model_name": "gemini-flash-latest",
        }
    )

    service = IncidentInvestigationService(
        hybrid_engine=mock_hybrid,
        gemini_service=mock_gemini,
    )

    request = InvestigationRequest(
        query="Why is payment service failing?",
        top_k=5,
        service_name="payment-service",
    )
    response = await service.investigate(request)

    assert response.investigation_id.startswith("inv_")
    assert response.query == "Why is payment service failing?"
    assert "recurring timeouts" in response.incident_summary
    assert response.affected_services == ["payment-service"]
    assert response.severity_assessment == "HIGH"
    assert len(response.key_observations) == 1
    assert response.key_observations[0].is_fact is True
    assert len(response.potential_root_causes) == 1
    assert response.potential_root_causes[0].rank == 1

    # Check that authoritative metadata was populated from the real chunk
    assert len(response.supporting_evidence) >= 1
    ev_item = response.supporting_evidence[0]
    assert ev_item.chunk_id == "chunk_payment_1"
    assert ev_item.source_filename == "payment.log"
    assert ev_item.source_line_start == 10
    assert ev_item.source_line_end == 25
    assert ev_item.severity == "ERROR"

    assert response.evidence_sufficiency.status == "SUFFICIENT"
    assert response.evidence_sufficiency.confidence_score == 0.9
    assert response.model_information.model_name == "gemini-flash-latest"
    assert response.retrieved_chunks_count == 2


@pytest.mark.asyncio
async def test_investigate_empty_retrieval_returns_insufficient_evidence():
    """Verify that when no logs match the query, an explicit un-hallucinated response is returned."""
    mock_hybrid = MagicMock()
    mock_hybrid.search.return_value = []

    mock_gemini = MagicMock()
    mock_gemini.model_name = "gemini-flash-latest"

    service = IncidentInvestigationService(
        hybrid_engine=mock_hybrid,
        gemini_service=mock_gemini,
    )

    request = InvestigationRequest(query="Unheard of obscure error xyz_99812")
    response = await service.investigate(request)

    assert response.retrieved_chunks_count == 0
    assert response.evidence_sufficiency.status == "INSUFFICIENT"
    assert response.evidence_sufficiency.confidence_score == 0.0
    assert "No matching log records were retrieved" in response.incident_summary
    assert len(response.supporting_evidence) == 0
    # Gemini should NOT have been called
    mock_gemini.generate_json.assert_not_called()


@pytest.mark.asyncio
async def test_investigate_hallucinated_chunk_ids_filtered_and_grounded():
    """Verify that hallucinated chunk IDs from LLM output are dropped, and true chunks preserved."""
    mock_hybrid = MagicMock()
    chunk1 = create_mock_search_result("chunk_real_1", "Real log content", filename="auth.log")
    mock_hybrid.search.return_value = [chunk1]

    mock_gemini = MagicMock()
    mock_gemini.model_name = "gemini-flash-latest"
    mock_gemini.generate_json = AsyncMock(
        return_value={
            "data": {
                "incident_summary": "Summary",
                "affected_services": ["auth-service"],
                "key_observations": [
                    {
                        "observation": "Observation",
                        "category": "ERROR",
                        "is_fact": True,
                        "evidence_chunk_ids": ["chunk_real_1", "chunk_fake_999"],  # fake chunk
                    }
                ],
                "potential_root_causes": [
                    {
                        "rank": 1,
                        "hypothesis": "Hypothesis",
                        "reasoning": "Reason",
                        "confidence": "MEDIUM",
                        "confidence_reasoning": "Reasoning",
                        "supporting_evidence_ids": ["chunk_fake_999"],  # fake chunk
                    }
                ],
                "supporting_evidence": [
                    {
                        "chunk_id": "chunk_fake_999",  # hallucinated chunk
                        "relevant_excerpt": "Fabricated log line",
                        "relevance_explanation": "Fake explanation",
                    }
                ],
            },
            "latency_ms": 150.0,
        }
    )

    service = IncidentInvestigationService(
        hybrid_engine=mock_hybrid,
        gemini_service=mock_gemini,
    )

    request = InvestigationRequest(query="Auth failure")
    response = await service.investigate(request)

    # Fake chunk_id should be filtered out of observation references
    assert "chunk_fake_999" not in response.key_observations[0].evidence_chunk_ids
    assert "chunk_real_1" in response.key_observations[0].evidence_chunk_ids

    # Fake chunk_id should be filtered out of root cause references
    assert "chunk_fake_999" not in response.potential_root_causes[0].supporting_evidence_ids

    # Fake chunk_id should NOT appear in supporting evidence; fallback should attach real chunk
    assert len(response.supporting_evidence) >= 1
    assert response.supporting_evidence[0].chunk_id == "chunk_real_1"
    assert response.supporting_evidence[0].source_filename == "auth.log"


@pytest.mark.asyncio
async def test_investigate_propagates_gemini_api_error():
    """Verify that upstream Gemini API failures are propagated properly without fake responses."""
    mock_hybrid = MagicMock()
    mock_hybrid.search.return_value = [create_mock_search_result("c1", "log content")]

    mock_gemini = MagicMock()
    mock_gemini.generate_json = AsyncMock(
        side_effect=GeminiAPIError("Upstream Gemini failure")
    )

    service = IncidentInvestigationService(
        hybrid_engine=mock_hybrid,
        gemini_service=mock_gemini,
    )

    with pytest.raises(GeminiAPIError):
        await service.investigate(InvestigationRequest(query="Failure test"))

