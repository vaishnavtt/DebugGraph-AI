"""
API integration tests for the /api/v1/analysis/investigate endpoint.
Tests validation, successful investigations, empty retrieval responses,
and centralized error handling (503, 429, 504, 502).
"""
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
import pytest

from app.api.analysis import get_investigation_service
from app.core.errors import (
    GeminiAPIError,
    GeminiConfigurationError,
    GeminiRateLimitError,
    GeminiTimeoutError,
)
from app.main import app
from app.schemas.investigation import (
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


def create_mock_investigation_response(
    query: str = "Why is the payment service failing?",
    status: str = "SUFFICIENT",
) -> InvestigationResponse:
    """Helper creating a complete InvestigationResponse."""
    return InvestigationResponse(
        investigation_id="inv_test_123456",
        query=query,
        incident_summary="Payment gateway timeout identified.",
        affected_services=["payment-service"],
        severity_assessment="HIGH",
        key_observations=[
            KeyObservation(
                observation="Downstream timeout contacting Stripe API",
                category="EXCEPTION",
                is_fact=True,
                timestamp="2026-11-01T10:00:00Z",
                affected_service="payment-service",
                evidence_chunk_ids=["chunk_1"],
            )
        ],
        potential_root_causes=[
            PotentialRootCause(
                rank=1,
                hypothesis="External payment gateway latency",
                reasoning="Egress calls timed out after 30 seconds",
                confidence="HIGH",
                confidence_reasoning="Direct stack traces in logs",
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
                relevant_excerpt="ConnectionTimeoutError: Stripe timeout",
                relevance_explanation="Shows the exact outbound call timeout",
            )
        ],
        recommended_actions=[
            RecommendedAction(
                priority=1,
                action="Check Stripe status page and internal NAT gateway",
                category="IMMEDIATE_MITIGATION",
                rationale="Isolate internal vs external network fault",
            )
        ],
        further_investigation=FurtherInvestigation(
            missing_evidence=["Network flow logs"],
            recommended_checks=["curl -Iv https://api.stripe.com"],
        ),
        evidence_sufficiency=EvidenceSufficiency(
            status=status,
            reason="Correlated log lines present.",
            confidence_score=0.9,
        ),
        model_information=ModelInformation(
            model_name="gemini-flash-latest",
            provider="Google Gemini",
            prompt_tokens=300,
            completion_tokens=150,
            total_tokens=450,
            latency_ms=210.0,
        ),
        retrieved_chunks_count=1,
        created_at="2026-11-01T10:05:00Z",
    )


def test_investigate_endpoint_success():
    """Verify POST /api/v1/analysis/investigate returns HTTP 200 with structured report."""
    mock_service = MagicMock()
    mock_service.investigate = AsyncMock(
        return_value=create_mock_investigation_response()
    )

    app.dependency_overrides[get_investigation_service] = lambda: mock_service

    try:
        response = client.post(
            "/api/v1/analysis/investigate",
            json={
                "query": "Why is the payment service failing?",
                "top_k": 10,
                "service_name": "payment-service",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["investigation_id"] == "inv_test_123456"
        assert data["query"] == "Why is the payment service failing?"
        assert data["incident_summary"] == "Payment gateway timeout identified."
        assert data["affected_services"] == ["payment-service"]
        assert data["severity_assessment"] == "HIGH"
        assert len(data["key_observations"]) == 1
        assert len(data["potential_root_causes"]) == 1
        assert len(data["supporting_evidence"]) == 1
        assert data["supporting_evidence"][0]["source_filename"] == "payment.log"
        assert data["supporting_evidence"][0]["source_line_start"] == 15
        assert data["evidence_sufficiency"]["status"] == "SUFFICIENT"
    finally:
        app.dependency_overrides.pop(get_investigation_service, None)


def test_investigate_endpoint_validation_error():
    """Verify empty query or invalid top_k yields HTTP 422 with validation error envelope."""
    response = client.post(
        "/api/v1/analysis/investigate",
        json={"query": "", "top_k": 0},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"] is True
    assert data["code"] == "VALIDATION_ERROR"
    assert "details" in data


def test_investigate_endpoint_gemini_not_configured_returns_503():
    """Verify unconfigured Gemini API key returns HTTP 503."""
    mock_service = MagicMock()
    mock_service.investigate = AsyncMock(
        side_effect=GeminiConfigurationError("Gemini API key is not configured.")
    )

    app.dependency_overrides[get_investigation_service] = lambda: mock_service

    try:
        response = client.post(
            "/api/v1/analysis/investigate",
            json={"query": "Why is the payment service failing?"},
        )
        assert response.status_code == 503
        data = response.json()
        assert data["error"] is True
        assert data["code"] == "GEMINI_NOT_CONFIGURED"
        assert "not configured" in data["message"].lower()
    finally:
        app.dependency_overrides.pop(get_investigation_service, None)


def test_investigate_endpoint_rate_limit_returns_429():
    """Verify Gemini quota exhaustion returns HTTP 429."""
    mock_service = MagicMock()
    mock_service.investigate = AsyncMock(
        side_effect=GeminiRateLimitError("Gemini rate limit exceeded.")
    )

    app.dependency_overrides[get_investigation_service] = lambda: mock_service

    try:
        response = client.post(
            "/api/v1/analysis/investigate",
            json={"query": "Why is the payment service failing?"},
        )
        assert response.status_code == 429
        data = response.json()
        assert data["error"] is True
        assert data["code"] == "GEMINI_RATE_LIMIT"
    finally:
        app.dependency_overrides.pop(get_investigation_service, None)


def test_investigate_endpoint_timeout_returns_504():
    """Verify Gemini timeout returns HTTP 504."""
    mock_service = MagicMock()
    mock_service.investigate = AsyncMock(
        side_effect=GeminiTimeoutError("Gemini request timed out.")
    )

    app.dependency_overrides[get_investigation_service] = lambda: mock_service

    try:
        response = client.post(
            "/api/v1/analysis/investigate",
            json={"query": "Why is the payment service failing?"},
        )
        assert response.status_code == 504
        data = response.json()
        assert data["error"] is True
        assert data["code"] == "GEMINI_TIMEOUT"
    finally:
        app.dependency_overrides.pop(get_investigation_service, None)


def test_investigate_endpoint_api_error_returns_502():
    """Verify Gemini API failure returns HTTP 502."""
    mock_service = MagicMock()
    mock_service.investigate = AsyncMock(
        side_effect=GeminiAPIError("Upstream Gemini API error.")
    )

    app.dependency_overrides[get_investigation_service] = lambda: mock_service

    try:
        response = client.post(
            "/api/v1/analysis/investigate",
            json={"query": "Why is the payment service failing?"},
        )
        assert response.status_code == 502
        data = response.json()
        assert data["error"] is True
        assert data["code"] == "GEMINI_API_ERROR"
    finally:
        app.dependency_overrides.pop(get_investigation_service, None)

