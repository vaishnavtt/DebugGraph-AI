"""
Unit tests for LangGraph multi-agent nodes, state management, and supervisor routing.
All external LLM and vector database dependencies are mocked.
"""
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.agents.nodes import InvestigationNodes
from app.agents.state import InvestigationState
from app.agents.workflow import create_investigation_graph, supervisor_evidence_decision
from app.retrieval.hybrid_search import HybridSearchResult, RetrievalDiagnostics


def create_sample_chunk(
    chunk_id: str,
    content: str = "ERROR [auth-service] DB-1045 Access denied",
    service: str = "auth-service",
    severity: str = "ERROR",
) -> HybridSearchResult:
    """Helper creating a valid HybridSearchResult."""
    diag = RetrievalDiagnostics(
        chunk_id=chunk_id,
        retrieval_methods=["dense", "bm25"],
        dense_rank=1,
        bm25_rank=1,
        dense_score=0.9,
        bm25_score=10.0,
        rrf_score=0.03,
        reranker_score=3.5,
    )
    return HybridSearchResult(
        chunk_id=chunk_id,
        content=content,
        original_filename="auth.log",
        service_name=service,
        severity=severity,
        timestamp_start="2026-11-01T10:00:00Z",
        timestamp_end="2026-11-01T10:05:00Z",
        source_line_start=1,
        source_line_end=10,
        source_entry_ids=[f"{chunk_id}_e1"],
        exception_signatures=["AccessDeniedError"],
        dense_score=0.9,
        bm25_score=10.0,
        rrf_score=0.03,
        reranker_score=3.5,
        diagnostics=diag,
    )


def test_langgraph_initialization():
    """Verify that LangGraph compiles the StateGraph successfully."""
    mock_hybrid = MagicMock()
    mock_gemini = MagicMock()
    graph = create_investigation_graph(hybrid_engine=mock_hybrid, gemini_service=mock_gemini)
    assert graph is not None
    assert hasattr(graph, "ainvoke")


@pytest.mark.asyncio
async def test_supervisor_init_node():
    """Verify supervisor initialization establishes workflow state."""
    nodes = InvestigationNodes(hybrid_engine=MagicMock(), gemini_service=MagicMock())
    state: InvestigationState = {
        "investigation_id": "inv_test_init",
        "query": "Test query",
        "max_iterations": 2,
    }
    result = await nodes.supervisor_init_node(state)
    assert result["investigation_status"] == "IN_PROGRESS"
    assert result["max_iterations"] == 2
    assert len(result["agent_execution_trace"]) == 1
    assert result["agent_execution_trace"][0]["agent_name"] == "SupervisorAgent"


@pytest.mark.asyncio
async def test_log_investigator_node_success():
    """Verify Log Investigator retrieves and serializes evidence."""
    mock_hybrid = MagicMock()
    chunk1 = create_sample_chunk("chunk_1", service="payment-service")
    mock_hybrid.search.return_value = [chunk1]

    nodes = InvestigationNodes(hybrid_engine=mock_hybrid, gemini_service=MagicMock())
    state: InvestigationState = {
        "investigation_id": "inv_1",
        "query": "Payment timeout",
        "top_k": 5,
        "iteration_count": 0,
    }
    result = await nodes.log_investigator_node(state)

    assert result["iteration_count"] == 1
    assert len(result["retrieved_evidence"]) == 1
    assert result["retrieved_evidence"][0]["chunk_id"] == "chunk_1"
    assert "payment-service" in result["log_findings"]["affected_services"]
    assert len(result["agent_execution_trace"]) == 1
    assert result["agent_execution_trace"][0]["agent_name"] == "LogInvestigatorAgent"


@pytest.mark.asyncio
async def test_log_investigator_node_empty():
    """Verify Log Investigator handles zero search results without crashing."""
    mock_hybrid = MagicMock()
    mock_hybrid.search.return_value = []

    nodes = InvestigationNodes(hybrid_engine=mock_hybrid, gemini_service=MagicMock())
    state: InvestigationState = {
        "investigation_id": "inv_empty",
        "query": "Non-existent error",
        "top_k": 5,
        "iteration_count": 0,
    }
    result = await nodes.log_investigator_node(state)

    assert result["iteration_count"] == 1
    assert len(result["retrieved_evidence"]) == 0
    assert result["log_findings"]["retrieved_count"] == 0


@pytest.mark.asyncio
async def test_root_cause_analyst_node_with_evidence():
    """Verify Root Cause Analyst invokes Gemini and parses hypotheses."""
    mock_gemini = MagicMock()
    mock_gemini.model_name = "gemini-flash-latest"
    mock_gemini.generate_json = AsyncMock(
        return_value={
            "data": {
                "incident_summary": "Database authentication failure",
                "severity_assessment": "HIGH",
                "key_observations": [
                    {
                        "observation": "Access denied for user 'admin'",
                        "category": "EXCEPTION",
                        "is_fact": True,
                        "affected_service": "auth-service",
                        "evidence_chunk_ids": ["c1"],
                    }
                ],
                "hypotheses": [
                    {
                        "rank": 1,
                        "hypothesis": "Database password rotation out of sync",
                        "reasoning": "Auth denied error repeated 15 times",
                        "confidence": "HIGH",
                        "confidence_reasoning": "Direct DB-1045 logs",
                        "supporting_evidence_ids": ["c1"],
                    }
                ],
            }
        }
    )

    nodes = InvestigationNodes(hybrid_engine=MagicMock(), gemini_service=mock_gemini)
    state: InvestigationState = {
        "investigation_id": "inv_rca",
        "query": "Auth failure",
        "retrieved_evidence": [{"chunk_id": "c1", "original_filename": "auth.log", "content": "DB-1045"}],
    }
    result = await nodes.root_cause_analyst_node(state)

    assert len(result["root_cause_hypotheses"]) == 1
    assert result["root_cause_hypotheses"][0]["rank"] == 1
    assert result["root_cause_hypotheses"][0]["confidence"] == "HIGH"
    assert result["log_findings"]["severity_assessment"] == "HIGH"


@pytest.mark.asyncio
async def test_evidence_validator_rejects_hallucinated_citations():
    """Verify Evidence Validator rejects fake chunk IDs and updates confidence."""
    nodes = InvestigationNodes(hybrid_engine=MagicMock(), gemini_service=MagicMock())
    state: InvestigationState = {
        "retrieved_evidence": [{"chunk_id": "real_chunk_1"}],
        "root_cause_hypotheses": [
            {
                "rank": 1,
                "hypothesis": "Supported hypothesis",
                "confidence": "HIGH",
                "supporting_evidence_ids": ["real_chunk_1"],
            },
            {
                "rank": 2,
                "hypothesis": "Hallucinated hypothesis",
                "confidence": "HIGH",
                "supporting_evidence_ids": ["fake_chunk_999"],  # Fake chunk ID
            },
        ],
    }
    result = await nodes.evidence_validator_node(state)

    val_res = result["evidence_validation"]
    assert val_res["is_sufficient"] is True
    assert val_res["sufficiency_status"] == "SUFFICIENT"
    assert len(val_res["rejected_citations"]) == 1
    assert val_res["rejected_citations"][0]["hypothesis_rank"] == 2

    # Hallucinated hypothesis should have its citation stripped and confidence downgraded
    hyp2 = result["root_cause_hypotheses"][1]
    assert "fake_chunk_999" not in hyp2["supporting_evidence_ids"]
    assert hyp2["confidence"] == "LOW"


def test_supervisor_evidence_decision_routing():
    """Verify supervisor conditional routing decisions."""
    # 1. Zero evidence -> finalize_insufficient
    state_zero: InvestigationState = {
        "retrieved_evidence": [],
        "iteration_count": 1,
        "max_iterations": 2,
        "evidence_validation": {"is_sufficient": False, "sufficiency_status": "INSUFFICIENT"},
    }
    assert supervisor_evidence_decision(state_zero) == "finalize_insufficient"

    # 2. Insufficient evidence and iterations remain -> retry_retrieval
    state_retry: InvestigationState = {
        "retrieved_evidence": [{"chunk_id": "c1"}],
        "iteration_count": 1,
        "max_iterations": 2,
        "evidence_validation": {"is_sufficient": False, "sufficiency_status": "PARTIAL"},
    }
    assert supervisor_evidence_decision(state_retry) == "retry_retrieval"

    # 3. Insufficient evidence but max iterations reached -> proceed_to_resolution
    state_max_iters: InvestigationState = {
        "retrieved_evidence": [{"chunk_id": "c1"}],
        "iteration_count": 2,
        "max_iterations": 2,
        "evidence_validation": {"is_sufficient": False, "sufficiency_status": "PARTIAL"},
    }
    assert supervisor_evidence_decision(state_max_iters) == "proceed_to_resolution"

    # 4. Sufficient evidence -> proceed_to_resolution
    state_sufficient: InvestigationState = {
        "retrieved_evidence": [{"chunk_id": "c1"}],
        "iteration_count": 1,
        "max_iterations": 2,
        "evidence_validation": {"is_sufficient": True, "sufficiency_status": "SUFFICIENT"},
    }
    assert supervisor_evidence_decision(state_sufficient) == "proceed_to_resolution"

