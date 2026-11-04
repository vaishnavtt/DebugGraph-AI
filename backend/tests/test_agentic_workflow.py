"""
Integration tests for the complete compiled LangGraph multi-agent workflow.
Verifies end-to-end investigation execution, conditional loop bounds, and exception resilience.
"""
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.agents.nodes import InvestigationNodes
from app.agents.workflow import create_investigation_graph
from app.retrieval.hybrid_search import HybridSearchResult, RetrievalDiagnostics
from app.schemas.investigation import InvestigationRequest
from app.services.agentic_investigation_service import AgenticInvestigationService


def make_test_chunk(chunk_id: str, content: str, service: str = "payment-service") -> HybridSearchResult:
    diag = RetrievalDiagnostics(
        chunk_id=chunk_id,
        retrieval_methods=["dense", "bm25"],
        dense_rank=1,
        bm25_rank=1,
        dense_score=0.91,
        bm25_score=12.0,
        rrf_score=0.03,
        reranker_score=3.8,
    )
    return HybridSearchResult(
        chunk_id=chunk_id,
        content=content,
        original_filename="payment.log",
        service_name=service,
        severity="ERROR",
        timestamp_start="2026-11-01T10:00:00Z",
        timestamp_end="2026-11-01T10:05:00Z",
        source_line_start=15,
        source_line_end=30,
        source_entry_ids=[f"{chunk_id}_entry"],
        exception_signatures=["ConnectionTimeoutError"],
        dense_score=0.91,
        bm25_score=12.0,
        rrf_score=0.03,
        reranker_score=3.8,
        diagnostics=diag,
    )


@pytest.mark.asyncio
async def test_agentic_workflow_success_end_to_end():
    """Verify complete multi-agent workflow execution with all 5 specialized agents."""
    mock_hybrid = MagicMock()
    mock_hybrid.search.return_value = [
        make_test_chunk("c1", "ConnectionTimeoutError contacting Stripe API")
    ]

    mock_gemini = MagicMock()
    mock_gemini.model_name = "gemini-flash-latest"

    # Mock responses for RCA and Resolution Advisor
    def mock_generate_json(contents, system_instruction):
        if "Root Cause Analyst" in system_instruction:
            return {
                "data": {
                    "incident_summary": "Payment gateway latency spike caused socket timeouts",
                    "severity_assessment": "HIGH",
                    "key_observations": [
                        {
                            "observation": "Socket timeout contacting gateway",
                            "category": "EXCEPTION",
                            "is_fact": True,
                            "affected_service": "payment-service",
                            "evidence_chunk_ids": ["c1"],
                        }
                    ],
                    "hypotheses": [
                        {
                            "rank": 1,
                            "hypothesis": "External gateway degradation",
                            "reasoning": "ConnectionTimeoutError occurred consistently",
                            "confidence": "HIGH",
                            "confidence_reasoning": "Corroborated by stack traces in chunk c1",
                            "supporting_evidence_ids": ["c1"],
                        }
                    ],
                }
            }
        else:  # Resolution Advisor
            return {
                "data": {
                    "recommended_actions": [
                        {
                            "priority": 1,
                            "action": "Inspect gateway health and network routing",
                            "category": "IMMEDIATE_MITIGATION",
                            "rationale": "Isolate third-party outage from internal VPC",
                            "safety_warning": None,
                        }
                    ],
                    "further_investigation": {
                        "missing_evidence": ["NAT gateway metrics"],
                        "recommended_checks": ["curl -Iv https://api.stripe.com"],
                    },
                }
            }

    mock_gemini.generate_json = AsyncMock(side_effect=mock_generate_json)

    service = AgenticInvestigationService(
        hybrid_engine=mock_hybrid,
        gemini_service=mock_gemini,
    )

    request = InvestigationRequest(
        query="Why is the payment service failing?",
        top_k=5,
        service_name="payment-service",
    )
    response = await service.investigate(request)

    assert response.workflow_status == "SUCCESS"
    assert response.iterations_executed == 1
    assert response.investigation_id.startswith("inv_agent_")
    assert response.query == "Why is the payment service failing?"
    assert "Payment gateway latency spike" in response.incident_summary
    assert len(response.key_observations) == 1
    assert len(response.potential_root_causes) == 1
    assert response.potential_root_causes[0].rank == 1
    assert len(response.supporting_evidence) == 1
    assert response.supporting_evidence[0].chunk_id == "c1"
    assert len(response.recommended_actions) == 1

    # Verify agent execution trace contains all 5 agent stages
    agent_names = [t.agent_name for t in response.agent_execution_trace]
    assert "SupervisorAgent" in agent_names
    assert "LogInvestigatorAgent" in agent_names
    assert "RootCauseAnalystAgent" in agent_names
    assert "EvidenceValidatorAgent" in agent_names
    assert "ResolutionAdvisorAgent" in agent_names


@pytest.mark.asyncio
async def test_agentic_workflow_empty_retrieval_insufficient_evidence():
    """Verify that when 0 chunks are retrieved, the workflow routes directly to insufficient report."""
    mock_hybrid = MagicMock()
    mock_hybrid.search.return_value = []

    mock_gemini = MagicMock()
    mock_gemini.model_name = "gemini-flash-latest"

    service = AgenticInvestigationService(
        hybrid_engine=mock_hybrid,
        gemini_service=mock_gemini,
    )

    request = InvestigationRequest(query="Obscure unknown error code xyz_0099")
    response = await service.investigate(request)

    assert response.workflow_status == "INSUFFICIENT_EVIDENCE"
    assert response.retrieved_chunks_count == 0
    assert response.evidence_sufficiency.status == "INSUFFICIENT"
    assert "No matching log records were retrieved" in response.incident_summary


@pytest.mark.asyncio
async def test_agentic_workflow_bounded_retry_loop():
    """Verify that conditional retry routes back to retrieval and terminates at max_iterations."""
    mock_hybrid = MagicMock()
    # Return chunk on every search call
    mock_hybrid.search.return_value = [make_test_chunk("c1", "Log content")]

    mock_gemini = MagicMock()
    mock_gemini.model_name = "gemini-flash-latest"
    # Return a hypothesis with an invalid chunk ID to trigger insufficient validation on first pass
    mock_gemini.generate_json = AsyncMock(
        return_value={
            "data": {
                "incident_summary": "Summary",
                "severity_assessment": "MEDIUM",
                "hypotheses": [
                    {
                        "rank": 1,
                        "hypothesis": "Hypothesis",
                        "reasoning": "Reason",
                        "confidence": "LOW",
                        "supporting_evidence_ids": ["non_existent_chunk_99"],  # Invalid chunk -> insufficient
                    }
                ],
                "recommended_actions": [],
                "further_investigation": {},
            }
        }
    )

    service = AgenticInvestigationService(
        hybrid_engine=mock_hybrid,
        gemini_service=mock_gemini,
    )

    request = InvestigationRequest(query="Investigate retry loop")
    response = await service.investigate(request)

    # Workflow must terminate bounded at max_iterations (2)
    assert response.iterations_executed <= 2
    assert response.workflow_status in ("PARTIAL", "SUCCESS", "INSUFFICIENT_EVIDENCE")


@pytest.mark.asyncio
async def test_agentic_workflow_handles_unhandled_graph_exception():
    """Verify that a fatal unexpected error in graph execution builds a clean FAILED response."""
    mock_hybrid = MagicMock()
    mock_hybrid.search.side_effect = RuntimeError("Fatal hardware I/O error")

    service = AgenticInvestigationService(
        hybrid_engine=mock_hybrid,
        gemini_service=MagicMock(),
    )

    request = InvestigationRequest(query="Fatal test")
    response = await service.investigate(request)

    # Should not raise an unhandled server error, but return a grounded FAILED report
    assert response.workflow_status in ("FAILED", "INSUFFICIENT_EVIDENCE")
    assert response.retrieved_chunks_count == 0

