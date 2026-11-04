"""
Health and readiness check endpoints for DebugGraph AI.
Provides liveness validation and active dependency availability probes.
"""
import socket
from urllib.parse import urlparse
from fastapi import APIRouter, Response, status
import httpx
from sqlalchemy import create_engine, text

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.responses import HealthResponse, ReadinessResponse

logger = get_logger(__name__)

router = APIRouter()


def check_postgres_availability() -> str:
    """
    Check availability of configured PostgreSQL database.
    Does not use fake/mock connections; performs real ping with a strict timeout.
    """
    if not settings.DATABASE_URL:
        return "not_configured"

    try:
        # Strict 1.5s connection timeout for health probes
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"connect_timeout": 2},
            pool_pre_ping=False,
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "connected"
    except Exception as exc:
        logger.debug("Database health check failed: %s", exc)
        return "unavailable"


def check_neo4j_availability() -> str:
    """
    Check network reachability of configured Neo4j instance.
    Validates socket connection to the Bolt port with strict timeout.
    """
    if not settings.NEO4J_URI:
        return "not_configured"

    try:
        parsed = urlparse(settings.NEO4J_URI)
        host = parsed.hostname or "localhost"
        port = parsed.port or 7687

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.5)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            return "reachable"
        return "unavailable"
    except Exception as exc:
        logger.debug("Neo4j health check failed: %s", exc)
        return "unavailable"


async def check_qdrant_availability() -> str:
    """
    Check availability of configured Qdrant vector database via HTTP probe.
    """
    if not settings.QDRANT_URL:
        return "not_configured"

    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.get(f"{settings.QDRANT_URL.rstrip('/')}/healthz")
            if resp.status_code == 200:
                return "connected"
            return "unavailable"
    except Exception as exc:
        logger.debug("Qdrant health check failed: %s", exc)
        return "unavailable"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application Health / Liveness Probe",
    description="Returns the immediate liveness status of the FastAPI backend application.",
)
async def get_health() -> HealthResponse:
    """Liveness probe reporting application status and version."""
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment="development" if settings.DEBUG else "production",
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Dependency Readiness Probe",
    description="Validates active connectivity to configured database, graph, and vector dependencies.",
)
async def get_readiness(response: Response) -> ReadinessResponse:
    """Readiness probe evaluating true connectivity to configured downstream services."""
    services = {
        "database": check_postgres_availability(),
        "neo4j": check_neo4j_availability(),
        "qdrant": await check_qdrant_availability(),
    }

    # Determine if any actively configured dependency is unavailable
    has_unavailable = any(status == "unavailable" for status in services.values())

    if has_unavailable:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "not_ready"
    else:
        response.status_code = status.HTTP_200_OK
        overall_status = "ready"

    return ReadinessResponse(
        status=overall_status,
        services=services,
    )


@router.get(
    "/health/overview",
    summary="System Overview Metrics",
    description="Returns aggregate counts of uploaded logs, indexed chunks, graph services, health status, and active AI model for the frontend dashboard.",
)
async def get_overview() -> dict:
    """Aggregates telemetry, storage counts, and system status for the dashboard overview."""
    # 1. Check dependency status
    db_status = check_postgres_availability()
    neo_status = check_neo4j_availability()
    qdrant_status = await check_qdrant_availability()

    # 2. Query log and chunk counts from database
    total_logs = 0
    total_chunks = 0
    try:
        from app.database.models import IngestionRecord, LogChunkRecord
        from app.database.session import get_db_context

        with get_db_context() as session:
            total_logs = session.query(IngestionRecord).count()
            total_chunks = session.query(LogChunkRecord).count()
    except Exception as exc:
        logger.debug("Could not fetch database record counts: %s", exc)

    # 3. Query graph services count if available
    graph_services_count = 0
    try:
        from app.graph.manager import KnowledgeGraphManager
        mgr = KnowledgeGraphManager()
        if mgr.is_available():
            h = mgr.health_check()
            graph_services_count = (h.get("node_counts") or {}).get("services", 0)
    except Exception as exc:
        logger.debug("Could not fetch graph node counts: %s", exc)

    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEBUG else "production",
        "ai_model": settings.GEMINI_MODEL,
        "services": {
            "database": db_status,
            "neo4j": neo_status,
            "qdrant": qdrant_status,
        },
        "metrics": {
            "total_ingested_logs": total_logs,
            "total_indexed_chunks": total_chunks,
            "total_graph_services": graph_services_count,
            "github_integration_enabled": bool(settings.GITHUB_TOKEN and settings.GITHUB_TOKEN != "your_github_token_here_optional"),
        },
    }


