"""
Unit and integration tests for Neo4j Knowledge Graph driver, manager, and API endpoints.
All tests use robust mocking so they pass offline without requiring a live Neo4j daemon.
"""
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.graph.driver import Neo4jDriverManager
from app.graph.manager import KnowledgeGraphManager
from app.main import app

client = TestClient(app)


# =============================================================================
# 1. Neo4jDriverManager Tests
# =============================================================================

def test_driver_manager_connectivity_offline():
    """Verify driver manager handles offline connection gracefully."""
    with patch("app.graph.driver.GraphDatabase.driver") as mock_driver_fn:
        mock_driver = MagicMock()
        mock_driver.verify_connectivity.side_effect = Exception("Bolt connection refused")
        mock_driver_fn.return_value = mock_driver

        mgr = Neo4jDriverManager(uri="bolt://localhost:7687", username="neo4j", password="password")
        assert mgr.verify_connectivity() is False


def test_driver_manager_connectivity_success():
    """Verify driver manager reports connected when verify_connectivity succeeds."""
    with patch("app.graph.driver.GraphDatabase.driver") as mock_driver_fn:
        mock_driver = MagicMock()
        mock_driver.verify_connectivity.return_value = None
        mock_driver_fn.return_value = mock_driver

        mgr = Neo4jDriverManager(uri="bolt://localhost:7687", username="neo4j", password="password")
        assert mgr.verify_connectivity() is True


def test_driver_manager_execute_query():
    """Verify driver manager executes query through session context manager."""
    with patch("app.graph.driver.GraphDatabase.driver") as mock_driver_fn:
        mock_record = MagicMock()
        mock_record.data.return_value = {"name": "payment-service", "status": "active"}

        mock_session = MagicMock()
        mock_session.run.return_value = [mock_record]

        mock_driver = MagicMock()
        mock_driver.session.return_value = mock_session
        mock_driver_fn.return_value = mock_driver

        mgr = Neo4jDriverManager(uri="bolt://localhost:7687", username="neo4j", password="password")
        results = mgr.execute_query("MATCH (s:Service) RETURN s")
        assert len(results) == 1
        assert results[0]["name"] == "payment-service"


def test_driver_manager_init_schema():
    """Verify schema constraints are created idempotently."""
    with patch("app.graph.driver.GraphDatabase.driver") as mock_driver_fn:
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.verify_connectivity.return_value = None
        mock_driver.session.return_value = mock_session
        mock_driver_fn.return_value = mock_driver

        mgr = Neo4jDriverManager(uri="bolt://localhost:7687", username="neo4j", password="password")
        success = mgr.init_schema()
        assert success is True
        assert mock_session.run.call_count >= 8


# =============================================================================
# 2. KnowledgeGraphManager Tests
# =============================================================================

def test_register_service():
    """Verify idempotent service registration generates proper Cypher execution."""
    mock_driver = MagicMock()
    mock_driver.execute_query.return_value = [{"name": "auth-service", "environment": "production", "status": "active"}]

    mgr = KnowledgeGraphManager(driver_manager=mock_driver)
    res = mgr.register_service(name="auth-service", environment="production", tier="backend")
    assert res["name"] == "auth-service"
    assert mock_driver.execute_query.called


def test_register_database_and_api():
    """Verify database and API entity registration."""
    mock_driver = MagicMock()
    mock_driver.execute_query.side_effect = [
        [{"name": "payments-db", "type": "postgresql"}],
        [{"name": "POST /api/v1/charge", "endpoint": "/api/v1/charge", "method": "POST"}],
    ]

    mgr = KnowledgeGraphManager(driver_manager=mock_driver)
    db_res = mgr.register_database(name="payments-db", db_type="postgresql")
    assert db_res["name"] == "payments-db"

    api_res = mgr.register_api(name="POST /api/v1/charge", endpoint="/api/v1/charge", method="POST")
    assert api_res["name"] == "POST /api/v1/charge"


def test_register_dependency_validation():
    """Verify invalid relationship type or node label raises ValueError to prevent injection."""
    mock_driver = MagicMock()
    mgr = KnowledgeGraphManager(driver_manager=mock_driver)

    with pytest.raises(ValueError, match="Invalid relationship type"):
        mgr.register_dependency(
            source="svc-a",
            target="svc-b",
            relation_type="INVALID_RELATION",
        )

    with pytest.raises(ValueError, match="Invalid node labels"):
        mgr.register_dependency(
            source="svc-a",
            target="svc-b",
            relation_type="DEPENDS_ON",
            source_type="MaliciousLabel`",
        )


def test_register_dependency_success():
    """Verify valid dependency registration succeeds."""
    mock_driver = MagicMock()
    mock_driver.execute_query.return_value = [
        {"source": "order-service", "target": "payment-service", "relation_type": "DEPENDS_ON"}
    ]

    mgr = KnowledgeGraphManager(driver_manager=mock_driver)
    res = mgr.register_dependency(
        source="order-service",
        target="payment-service",
        relation_type="DEPENDS_ON",
    )
    assert res["source"] == "order-service"
    assert res["target"] == "payment-service"


def test_get_service():
    """Verify service retrieval returns structured details and relations."""
    mock_driver = MagicMock()
    mock_driver.execute_query.return_value = [
        {
            "name": "payment-service",
            "environment": "production",
            "tier": "backend",
            "team": "payments-team",
            "status": "active",
            "metadata": '{"framework": "fastapi"}',
            "upstream_dependencies": ["order-service", "checkout-service"],
            "downstream_dependencies": ["auth-service"],
            "connected_databases": ["payments-db"],
            "connected_apis": ["POST /v1/auth/verify"],
            "repositories": ["https://github.com/my-org/payment-service"],
        }
    ]

    mgr = KnowledgeGraphManager(driver_manager=mock_driver)
    svc = mgr.get_service("payment-service")
    assert svc is not None
    assert svc["name"] == "payment-service"
    assert svc["upstream_dependencies"] == ["order-service", "checkout-service"]
    assert svc["downstream_dependencies"] == ["auth-service"]
    assert svc["connected_databases"] == ["payments-db"]
    assert svc["metadata"] == {"framework": "fastapi"}


def test_get_service_dependencies():
    """Verify bounded multi-hop dependency query execution."""
    mock_driver = MagicMock()
    # Downstream, db, api, upstream
    mock_driver.execute_query.side_effect = [
        [{"name": "inventory-service", "path_names": ["order-service", "inventory-service"]}],
        [{"db_name": "inventory-db"}],
        [{"api_name": "GET /stock"}],
        [{"name": "gateway-service", "path_names": ["gateway-service", "order-service"]}],
    ]

    mgr = KnowledgeGraphManager(driver_manager=mock_driver)
    deps = mgr.get_service_dependencies("order-service", direction="both", max_depth=2)
    assert deps["service_name"] == "order-service"
    assert "inventory-service" in deps["downstream"]
    assert "gateway-service" in deps["upstream"]
    assert "inventory-db" in deps["databases"]


def test_calculate_blast_radius():
    """Verify blast radius calculation and severity rating."""
    mock_driver = MagicMock()
    # Downstream, db, api, upstream, direct callers
    mock_driver.execute_query.side_effect = [
        [{"name": "auth-service", "path_names": ["payment-service", "auth-service"]}],
        [{"db_name": "payments-db"}],
        [],
        [
            {"name": "order-service", "path_names": ["order-service", "payment-service"]},
            {"name": "checkout-service", "path_names": ["checkout-service", "payment-service"]},
        ],
        [{"direct_callers": ["order-service", "checkout-service"]}],
    ]

    mgr = KnowledgeGraphManager(driver_manager=mock_driver)
    radius = mgr.calculate_blast_radius("payment-service")
    assert radius["service_name"] == "payment-service"
    assert radius["direct_dependents_count"] == 2
    assert "order-service" in radius["impacted_services"]
    assert "auth-service" in radius["impacted_services"]
    assert radius["blast_radius_score"] > 0.0
    assert radius["severity_level"] in ("CRITICAL", "HIGH", "MEDIUM", "LOW")


# =============================================================================
# 3. Knowledge Graph API Endpoint Tests
# =============================================================================

def test_api_register_service():
    """Verify POST /api/v1/graph/services endpoint."""
    with patch("app.api.graph.KnowledgeGraphManager.register_service") as mock_reg:
        mock_reg.return_value = {"name": "cart-service", "status": "active"}

        response = client.post(
            "/api/v1/graph/services",
            json={
                "name": "cart-service",
                "environment": "production",
                "tier": "backend",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "cart-service" in data["message"]


def test_api_register_dependency():
    """Verify POST /api/v1/graph/dependencies endpoint."""
    with patch("app.api.graph.KnowledgeGraphManager.register_dependency") as mock_dep:
        mock_dep.return_value = {
            "source": "frontend-service",
            "target": "api-gateway",
            "relation_type": "DEPENDS_ON",
        }

        response = client.post(
            "/api/v1/graph/dependencies",
            json={
                "source": "frontend-service",
                "target": "api-gateway",
                "relation_type": "DEPENDS_ON",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["source"] == "frontend-service"
        assert data["target"] == "api-gateway"


def test_api_get_service_detail():
    """Verify GET /api/v1/graph/services/{name} endpoint."""
    with patch("app.api.graph.KnowledgeGraphManager.get_service") as mock_get:
        mock_get.return_value = {
            "name": "billing-service",
            "environment": "production",
            "tier": "backend",
            "team": "finance",
            "status": "active",
            "metadata": {},
            "upstream_dependencies": ["payment-service"],
            "downstream_dependencies": [],
            "connected_databases": ["billing-db"],
            "connected_apis": [],
            "repositories": [],
        }

        response = client.get("/api/v1/graph/services/billing-service")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "billing-service"
        assert "payment-service" in data["upstream_dependencies"]


def test_api_get_service_not_found():
    """Verify GET /api/v1/graph/services/{name} returns 404 for unknown service."""
    with patch("app.api.graph.KnowledgeGraphManager.get_service") as mock_get:
        mock_get.return_value = None

        response = client.get("/api/v1/graph/services/nonexistent-service")
        assert response.status_code == 404


def test_api_get_blast_radius():
    """Verify GET /api/v1/graph/services/{name}/blast-radius endpoint."""
    with patch("app.api.graph.KnowledgeGraphManager.calculate_blast_radius") as mock_radius:
        mock_radius.return_value = {
            "service_name": "core-db-proxy",
            "blast_radius_score": 0.85,
            "severity_level": "CRITICAL",
            "direct_dependents_count": 8,
            "total_impacted_services_count": 12,
            "impacted_services": ["svc-1", "svc-2"],
            "impacted_databases": ["postgres-master"],
            "impacted_apis": [],
            "dependency_chains": [["svc-1", "core-db-proxy"]],
        }

        response = client.get("/api/v1/graph/services/core-db-proxy/blast-radius")
        assert response.status_code == 200
        data = response.json()
        assert data["service_name"] == "core-db-proxy"
        assert data["blast_radius_score"] == 0.85
        assert data["severity_level"] == "CRITICAL"


def test_api_graph_health():
    """Verify GET /api/v1/graph/health endpoint."""
    with patch("app.api.graph.KnowledgeGraphManager.health_check") as mock_health:
        mock_health.return_value = {
            "status": "healthy",
            "connected": True,
            "uri": "bolt://localhost:7687",
            "database": "neo4j",
            "node_counts": {"services": 5, "databases": 2},
            "error": None,
        }

        response = client.get("/api/v1/graph/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["connected"] is True
        assert data["node_counts"]["services"] == 5

