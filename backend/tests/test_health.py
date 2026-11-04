"""
Test suite for DebugGraph AI core endpoints:
- Root metadata endpoint
- Health / liveness probe
- Readiness / dependency probe
- Error response handling
"""
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    """Validate root endpoint returns operational metadata and navigation links."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "online"
    assert data["app_name"] == settings.APP_NAME
    assert data["version"] == settings.APP_VERSION
    assert "/docs" in data["docs_url"]
    assert "/health" in data["health_url"]
    assert "/health/ready" in data["readiness_url"]


def test_health_endpoint() -> None:
    """Validate liveness probe at /api/v1/health and top-level alias /health."""
    for path in [f"{settings.API_V1_PREFIX}/health", "/health"]:
        response = client.get(path)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["app_name"] == settings.APP_NAME
        assert data["version"] == settings.APP_VERSION
        assert "environment" in data
        assert "timestamp" in data


def test_api_response_structure() -> None:
    """Verify that responses conform to the standardized schema formats."""
    response = client.get(f"{settings.API_V1_PREFIX}/health")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    data = response.json()
    required_keys = {"status", "app_name", "version", "environment", "timestamp"}
    assert required_keys.issubset(data.keys())


def test_invalid_endpoint_handling() -> None:
    """Verify that requests to non-existent routes return the standardized ErrorResponse JSON envelope."""
    response = client.get(f"{settings.API_V1_PREFIX}/non-existent-endpoint")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/json"

    data = response.json()
    assert data["error"] is True
    assert data["code"] == "NOT_FOUND"
    assert "message" in data
    assert "timestamp" in data


def test_readiness_endpoint_unconnected_behavior() -> None:
    """
    Verify that when downstream services are unreachable, the readiness probe:
    1. Returns HTTP 503 Service Unavailable.
    2. Reports status as 'not_ready'.
    3. Accurately reports 'unavailable' rather than pretending services are healthy.
    """
    response = client.get(f"{settings.API_V1_PREFIX}/health/ready")

    # In local testing without active DB/Neo4j/Qdrant containers, dependencies should report unavailable
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "timestamp" in data

    services = data["services"]
    assert "database" in services
    assert "neo4j" in services
    assert "qdrant" in services

    # If any service is unavailable, overall readiness must be 503 and 'not_ready'
    if any(s == "unavailable" for s in services.values()):
        assert response.status_code == 503
        assert data["status"] == "not_ready"
    else:
        assert response.status_code == 200
        assert data["status"] == "ready"


def test_readiness_endpoint_when_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verify that when dependencies are intentionally unconfigured,
    the system reports 'not_configured' and remains in a 'ready' state.
    """
    monkeypatch.setattr(settings, "DATABASE_URL", None)
    monkeypatch.setattr(settings, "NEO4J_URI", None)
    monkeypatch.setattr(settings, "QDRANT_URL", None)

    response = client.get(f"{settings.API_V1_PREFIX}/health/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert data["services"]["database"] == "not_configured"
    assert data["services"]["neo4j"] == "not_configured"
    assert data["services"]["qdrant"] == "not_configured"

