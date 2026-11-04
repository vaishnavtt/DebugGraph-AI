"""
Unit and integration tests for Graph Investigator and GitHub Investigator Agents
within the 7-agent LangGraph workflow.
"""
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.agents.nodes import InvestigationNodes
from app.agents.state import InvestigationState
from app.agents.workflow import create_investigation_graph
from app.graph.manager import KnowledgeGraphManager
from app.retrieval.hybrid_search import HybridSearchEngine, HybridSearchResult, RetrievalDiagnostics
from app.schemas.investigation import InvestigationRequest
from app.services.agentic_investigation_service import AgenticInvestigationService
from app.services.gemini_service import GeminiService
from app.services.github_service import GitHubService


# =============================================================================
# 1. Graph Investigator Agent Node Tests
# =============================================================================

@pytest.mark.asyncio
async def test_graph_investigator_node_success():
    """Verify Graph Investigator queries service topology and blast radius when Neo4j is available."""
    mock_graph_mgr = MagicMock(spec=KnowledgeGraphManager)
    mock_graph_mgr.is_available.return_value = True
    mock_graph_mgr.get_service.return_value = {
        "name": "payment-service",
        "environment": "production",
        "upstream_dependencies": ["order-service"],
        "downstream_dependencies": ["auth-service"],
        "connected_databases": ["payments-db"],
        "connected_apis": [],
    }
    mock_graph_mgr.get_service_dependencies.return_value = {
        "service_name": "payment-service",
        "upstream": ["order-service"],
        "downstream": ["auth-service"],
        "databases": ["payments-db"],
        "apis": [],
        "traversal_paths": [["order-service", "payment-service", "auth-service"]],
    }
    mock_graph_mgr.calculate_blast_radius.return_value = {
        "service_name": "payment-service",
        "blast_radius_score": 0.65,
        "severity_level": "HIGH",
        "direct_dependents_count": 1,
        "total_impacted_services_count": 2,
        "impacted_services": ["order-service", "auth-service"],
        "impacted_databases": ["payments-db"],
        "impacted_apis": [],
        "dependency_chains": [],
    }
    mock_graph_mgr.get_related_errors.return_value = []

    nodes = InvestigationNodes(graph_manager=mock_graph_mgr)
    state: InvestigationState = {
        "service_name": "payment-service",
        "log_findings": {"affected_services": ["payment-service"]},
        "agent_execution_trace": [],
    }

    result = await nodes.graph_investigator_node(state)
    assert result["graph_evidence"]["status"] == "completed"
    assert result["graph_evidence"]["primary_service"] == "payment-service"
    assert result["blast_radius"]["blast_radius_score"] == 0.65
    assert len(result["agent_execution_trace"]) == 1
    assert result["agent_execution_trace"][0]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_graph_investigator_node_offline():
    """Verify Graph Investigator degrades gracefully without error when Neo4j is offline."""
    mock_graph_mgr = MagicMock(spec=KnowledgeGraphManager)
    mock_graph_mgr.is_available.return_value = False

    nodes = InvestigationNodes(graph_manager=mock_graph_mgr)
    state: InvestigationState = {
        "service_name": "payment-service",
        "agent_execution_trace": [],
    }

    result = await nodes.graph_investigator_node(state)
    assert result["graph_evidence"]["status"] == "unavailable"
    assert result["blast_radius"] is None
    assert result["agent_execution_trace"][0]["status"] == "SKIPPED"


@pytest.mark.asyncio
async def test_graph_investigator_node_no_service():
    """Verify Graph Investigator skips gracefully when no service is identified."""
    mock_graph_mgr = MagicMock(spec=KnowledgeGraphManager)
    mock_graph_mgr.is_available.return_value = True

    nodes = InvestigationNodes(graph_manager=mock_graph_mgr)
    state: InvestigationState = {
        "service_name": None,
        "log_findings": {"affected_services": []},
        "agent_execution_trace": [],
    }

    result = await nodes.graph_investigator_node(state)
    assert result["graph_evidence"]["status"] == "skipped"
    assert result["agent_execution_trace"][0]["status"] == "SKIPPED"


# =============================================================================
# 2. GitHub Investigator Agent Node Tests
# =============================================================================

@pytest.mark.asyncio
async def test_github_investigator_node_success():
    """Verify GitHub Investigator correlates commits when service is linked to repo."""
    mock_graph_mgr = MagicMock(spec=KnowledgeGraphManager)
    mock_graph_mgr.is_available.return_value = True
    mock_graph_mgr.get_repo_for_service.return_value = "https://github.com/my-org/payment-service"

    mock_github_svc = MagicMock(spec=GitHubService)
    mock_github_svc.correlate_commits_with_incident = AsyncMock(
        return_value={
            "repository": "my-org/payment-service",
            "commits_inspected_count": 5,
            "has_candidate_commits": True,
            "candidate_commits": [
                {
                    "sha": "abc1234567890",
                    "short_sha": "abc1234",
                    "repository": "my-org/payment-service",
                    "author": "Alice",
                    "date": "2026-11-04T12:00:00Z",
                    "relevance_score": 0.85,
                    "suspect_files": ["db/pool.py"],
                    "diff_excerpt": "- pool_size = 20\n+ pool_size = 2",
                    "correlation_reasoning": "Reduced database pool size right before connection timeout spikes.",
                }
            ],
            "analysis_summary": "Identified 1 candidate commit in my-org/payment-service.",
        }
    )

    nodes = InvestigationNodes(
        graph_manager=mock_graph_mgr,
        github_service=mock_github_svc,
    )
    state: InvestigationState = {
        "service_name": "payment-service",
        "log_findings": {
            "affected_services": ["payment-service"],
            "error_signatures": ["timeout error in pool"],
        },
        "agent_execution_trace": [],
    }

    result = await nodes.github_investigator_node(state)
    assert result["github_evidence"]["has_candidate_commits"] is True
    assert len(result["github_evidence"]["candidate_commits"]) == 1
    assert result["agent_execution_trace"][0]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_github_investigator_node_no_repo():
    """Verify GitHub Investigator skips gracefully when no repo is associated."""
    mock_graph_mgr = MagicMock(spec=KnowledgeGraphManager)
    mock_graph_mgr.is_available.return_value = True
    mock_graph_mgr.get_repo_for_service.return_value = None

    nodes = InvestigationNodes(graph_manager=mock_graph_mgr)
    state: InvestigationState = {
        "service_name": "unknown-service",
        "query": "generic error query",
        "log_findings": {"affected_services": []},
        "agent_execution_trace": [],
    }

    result = await nodes.github_investigator_node(state)
    assert result["github_evidence"]["status"] == "skipped"
    assert result["agent_execution_trace"][0]["status"] == "SKIPPED"


# =============================================================================
# 3. Full 7-Agent End-to-End Workflow Test
# =============================================================================

@pytest.mark.asyncio
async def test_full_7_agent_workflow():
    """
    Verify end-to-end execution of the 7-agent LangGraph workflow:
    Supervisor -> Log Investigator -> Graph Investigator -> GitHub Investigator
    -> Root Cause Analyst -> Evidence Validator -> Resolution Advisor -> Supervisor Finalize.
    """
    # 1. Mock Hybrid Search Engine
    diag = RetrievalDiagnostics(
        chunk_id="chk_test_101",
        retrieval_methods=["dense", "bm25"],
        dense_rank=1,
        bm25_rank=1,
        dense_score=0.90,
        bm25_score=15.0,
        rrf_score=0.03,
        reranker_score=0.95,
    )
    mock_chunk = HybridSearchResult(
        chunk_id="chk_test_101",
        content="2026-11-04 12:00:00 [ERROR] payment-service: ConnectionRefusedError: pool exhausted",
        original_filename="payment_err.log",
        service_name="payment-service",
        severity="ERROR",
        timestamp_start="2026-11-04T12:00:00Z",
        timestamp_end="2026-11-04T12:00:00Z",
        source_line_start=10,
        source_line_end=15,
        source_entry_ids=["chk_test_101_e1"],
        exception_signatures=["ConnectionRefusedError"],
        dense_score=0.90,
        bm25_score=15.0,
        rrf_score=0.03,
        reranker_score=0.95,
        diagnostics=diag,
    )
    mock_hybrid = MagicMock(spec=HybridSearchEngine)
    mock_hybrid.search.return_value = [mock_chunk]

    # 2. Mock Gemini LLM
    mock_gemini = MagicMock(spec=GeminiService)
    mock_gemini.model_name = "gemini-flash-latest"

    # LLM returns for Root Cause Analyst and Resolution Advisor
    rca_return = {
        "status": "success",
        "data": {
            "incident_summary": "Payment service database connection pool exhausted following pool reduction.",
            "severity_assessment": "HIGH",
            "key_observations": [
                {
                    "observation": "Connection pool exhausted",
                    "category": "ERROR",
                    "is_fact": True,
                    "affected_service": "payment-service",
                    "timestamp": "2026-11-04T12:00:00Z",
                    "evidence_chunk_ids": ["chk_test_101"],
                }
            ],
            "hypotheses": [
                {
                    "rank": 1,
                    "hypothesis": "PostgreSQL pool depletion caused by commit reducing pool size from 20 to 2.",
                    "reasoning": "Verified by log error and matching commit diff.",
                    "confidence": "HIGH",
                    "confidence_reasoning": "Chunk chk_test_101 directly cites ConnectionRefusedError.",
                    "supporting_evidence_ids": ["chk_test_101"],
                }
            ],
        },
    }

    res_advisor_return = {
        "status": "success",
        "data": {
            "recommended_actions": [
                {
                    "priority": 1,
                    "action": "Revert commit abc1234 or increase database connection pool size",
                    "category": "MITIGATION",
                    "rationale": "Restores pool capacity to withstand incoming transaction concurrency.",
                    "safety_warning": None,
                }
            ],
            "further_investigation": {
                "missing_evidence": [],
                "recommended_checks": ["Monitor active connection count on payments-db"],
            },
        },
    }

    mock_gemini.generate_json = AsyncMock(side_effect=[rca_return, res_advisor_return])

    # 3. Mock Graph Manager
    mock_graph_mgr = MagicMock(spec=KnowledgeGraphManager)
    mock_graph_mgr.is_available.return_value = True
    mock_graph_mgr.get_service.return_value = {
        "name": "payment-service",
        "environment": "production",
        "upstream_dependencies": ["order-service"],
        "downstream_dependencies": [],
        "connected_databases": ["payments-db"],
        "connected_apis": [],
    }
    mock_graph_mgr.get_service_dependencies.return_value = {
        "service_name": "payment-service",
        "upstream": ["order-service"],
        "downstream": [],
        "databases": ["payments-db"],
        "apis": [],
        "traversal_paths": [],
    }
    mock_graph_mgr.calculate_blast_radius.return_value = {
        "service_name": "payment-service",
        "blast_radius_score": 0.55,
        "severity_level": "HIGH",
        "direct_dependents_count": 1,
        "total_impacted_services_count": 1,
        "impacted_services": ["order-service"],
        "impacted_databases": ["payments-db"],
        "impacted_apis": [],
        "dependency_chains": [],
    }
    mock_graph_mgr.get_related_errors.return_value = []
    mock_graph_mgr.get_repo_for_service.return_value = "https://github.com/my-org/payment-service"

    # 4. Mock GitHub Service
    mock_github_svc = MagicMock(spec=GitHubService)
    mock_github_svc.correlate_commits_with_incident = AsyncMock(
        return_value={
            "repository": "my-org/payment-service",
            "commits_inspected_count": 3,
            "has_candidate_commits": True,
            "candidate_commits": [
                {
                    "sha": "abc1234567890",
                    "short_sha": "abc1234",
                    "repository": "my-org/payment-service",
                    "author": "Alice",
                    "date": "2026-11-04T12:00:00Z",
                    "relevance_score": 0.90,
                    "suspect_files": ["db/pool.py"],
                    "diff_excerpt": "- pool_size = 20\n+ pool_size = 2",
                    "correlation_reasoning": "Pool size reduction matches ConnectionRefusedError.",
                }
            ],
            "analysis_summary": "Found 1 highly correlated commit.",
        }
    )

    # 5. Initialize Service & Run Investigation
    service = AgenticInvestigationService(
        hybrid_engine=mock_hybrid,
        gemini_service=mock_gemini,
        graph_manager=mock_graph_mgr,
        github_service=mock_github_svc,
    )

    request = InvestigationRequest(
        query="Why is payment-service throwing ConnectionRefusedError?",
        service_name="payment-service",
        top_k=5,
    )

    response = await service.investigate(request)

    # Verify Response Contract
    assert response.workflow_status == "SUCCESS"
    assert response.investigation_id.startswith("inv_agent_")
    assert response.retrieved_chunks_count == 1
    assert len(response.potential_root_causes) == 1
    assert response.potential_root_causes[0].supporting_evidence_ids == ["chk_test_101"]

    # Verify Graph Evidence & Blast Radius
    assert response.graph_evidence is not None
    assert response.graph_evidence.get("status") == "completed"
    assert response.blast_radius is not None
    assert response.blast_radius.get("blast_radius_score") == 0.55

    # Verify GitHub Evidence
    assert response.github_evidence is not None
    assert response.github_evidence.get("has_candidate_commits") is True
    assert len(response.github_evidence.get("candidate_commits", [])) == 1

    # Verify Agent Trace contains all 7 stages
    agent_stages = [t.stage for t in response.agent_execution_trace]
    assert "supervisor_init" in agent_stages
    assert "log_investigator" in agent_stages
    assert "graph_investigator" in agent_stages
    assert "github_investigator" in agent_stages
    assert "root_cause_analyst" in agent_stages
    assert "evidence_validator" in agent_stages
    assert "resolution_advisor" in agent_stages
    assert "supervisor_finalize" in agent_stages
