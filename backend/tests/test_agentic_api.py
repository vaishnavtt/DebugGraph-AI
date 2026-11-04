"""
API integration tests for POST /api/v1/analysis/investigate/agentic.
Verifies payload validation, agentic response contracts, trace observability,
and backward compatibility of the existing single-pass endpoint.
"""
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
import pytest

from app.api.analysis import get_agentic_investigation_service, get_investigation_service
from app.main import app
from app.schemas.investigation import (
    AgentExecutionStep,
    AgenticInvestigationResponse,
    EvidenceSufficiency,
    FurtherInvestigation,
    InvestigationResponse,
    KeyObservation,
    ModelInformation,
    PotentialRootCause,
    RecommendedAction,
    SupportingEvidenceItem,
)

client = TestClient(app)


def make_sample_agentic_response() -> AgenticInvestigationResponse:
    """Helper returning a populated AgenticInvestigationResponse."""
    return AgenticInvestigationResponse(
        investigation_id="inv_agent_123456",
        query="Why is the payment service failing?",
        incident_summary="Payment service socket timeout verified across 5 agents.",
        affected_services=["payment-service"],
        severity_assessment="HIGH",
        key_observations=[
            KeyObservation(
                observation="ConnectionTimeoutError in /app/payment/gateway.py",
                category="EXCEPTION",
                is_fact=True,
                affected_service="payment-service",
                evidence_chunk_ids=["chunk_1"],
            )
        ],
        potential_root_causes=[
            PotentialRootCause(
                rank=1,
                hypothesis="External payment gateway latency",
                reasoning="Socket timed out after 30 seconds",
                confidence="HIGH",
                confidence_reasoning="Direct stack traces verified by EvidenceValidatorAgent",
                supporting_evidence_ids=["chunk_1"],
            )
        ],
        supporting_evidence=[
            SupportingEvidenceItem(
                chunk_id="chunk_1",
                source_filename="payment.log",
                source_line_start=15,
                source_line_end=30,
                timestamp="2026-11-01T10:00:00Z",
                service_name="payment-service",
                severity="ERROR",
                relevant_excerpt="ConnectionTimeoutError contacting Stripe",
                relevance_explanation="Validated evidence chunk",
            )
        ],
        recommended_actions=[
            RecommendedAction(
                priority=1,
                action="Verify gateway status and egress NAT routing",
                category="IMMEDIATE_MITIGATION",
                rationale="Isolate internal vs external network degradation",
            )
        ],
        further_investigation=FurtherInvestigation(
            missing_evidence=["VPC Flow logs"],
            recommended_checks=["curl -Iv https://api.stripe.com"],
        ),
        evidence_sufficiency=EvidenceSufficiency(
            status="SUFFICIENT",
            reason="Verified empirical evidence from log streams.",
            confidence_score=0.9,
        ),
        model_information=ModelInformation(
            model_name="gemini-flash-latest",
            provider="Google Gemini (LangGraph Multi-Agent)",
        ),
        retrieved_chunks_count=1,
        created_at="2026-11-01T10:05:00Z",
        workflow_status="SUCCESS",
        iterations_executed=1,
        agent_execution_trace=[
            AgentExecutionStep(
                agent_name="SupervisorAgent",
                stage="supervisor_init",
                status="COMPLETED",
                timestamp="2026-11-01T10:00:00Z",
                summary="Initialized session",
                latency_ms=1.2,
            ),
            AgentExecutionStep(
                agent_name="LogInvestigatorAgent",
                stage="log_investigator",
                status="COMPLETED",
                timestamp="2026-11-01T10:00:01Z",
                summary="Retrieved 1 evidence chunk",
                latency_ms=45.0,
            ),
            AgentExecutionStep(
                agent_name="RootCauseAnalystAgent",
                stage="root_cause_analyst",
                status="COMPLETED",
                timestamp="2026-11-01T10:00:02Z",
                summary="Formulated 1 hypothesis",
                latency_ms=310.0,
            ),
            AgentExecutionStep(
                agent_name="EvidenceValidatorAgent",
                stage="evidence_validator",
                status="COMPLETED",
                timestamp="2026-11-01T10:00:03Z",
                summary="Validated 1 hypothesis",
                latency_ms=2.5,
            ),
            AgentExecutionStep(
                agent_name="ResolutionAdvisorAgent",
                stage="resolution_advisor",
                status="COMPLETED",
                timestamp="2026-11-01T10:00:04Z",
                summary="Formulated recommendations",
                latency_ms=180.0,
            ),
        ],
    )


def test_agentic_endpoint_success():
    """Verify POST /api/v1/analysis/investigate/agentic returns HTTP 200 with multi-agent report."""
    mock_service = MagicMock()
    mock_service.investigate = AsyncMock(return_value=make_sample_agentic_response())

    app.dependency_overrides[get_agentic_investigation_service] = lambda: mock_service

    try:
        response = client.post(
            "/api/v1/analysis/investigate/agentic",
            json={
                "query": "Why is the payment service failing?",
                "top_k": 5,
                "service_name": "payment-service",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["investigation_id"] == "inv_agent_123456"
        assert data["workflow_status"] == "SUCCESS"
        assert data["iterations_executed"] == 1
        assert len(data["agent_execution_trace"]) == 5
        agent_names = [s["agent_name"] for s in data["agent_execution_trace"]]
        assert "SupervisorAgent" in agent_names
        assert "LogInvestigatorAgent" in agent_names
        assert "EvidenceValidatorAgent" in agent_names
    finally:
        app.dependency_overrides.pop(get_agentic_investigation_service, None)


def test_agentic_endpoint_validation_error():
    """Verify invalid payloads (empty query or invalid top_k) return HTTP 422."""
    response = client.post(
        "/api/v1/analysis/investigate/agentic",
        json={"query": "", "top_k": 0},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"] is True
    assert data["code"] == "VALIDATION_ERROR"


def test_existing_single_pass_endpoint_compatibility():
    """Verify that adding the agentic endpoint did not break the existing single-pass endpoint."""
    mock_single_service = MagicMock()
    mock_single_service.investigate = AsyncMock(
        return_value=InvestigationResponse(
            investigation_id="inv_single_pass",
            query="Single pass test",
            incident_summary="Single pass summary",
            affected_services=["auth-service"],
            severity_assessment="MEDIUM",
            key_observations=[],
            potential_root_causes=[],
            supporting_evidence=[],
            recommended_actions=[],
            further_investigation=FurtherInvestigation(),
            evidence_sufficiency=EvidenceSufficiency(
                status="SUFFICIENT", reason="Valid", confidence_score=0.8
            ),
            model_information=ModelInformation(
                model_name="gemini-flash-latest", provider="Google Gemini"
            ),
            retrieved_chunks_count=1,
            created_at="2026-11-01T10:00:00Z",
        )
    )

    app.dependency_overrides[get_investigation_service] = lambda: mock_single_service

    try:
        response = client.post(
            "/api/v1/analysis/investigate",
            json={"query": "Single pass test"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["investigation_id"] == "inv_single_pass"
        assert data["incident_summary"] == "Single pass summary"
    finally:
        app.dependency_overrides.pop(get_investigation_service, None)

