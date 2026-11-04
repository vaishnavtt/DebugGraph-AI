"""
FastAPI endpoints for Neo4j Knowledge Graph operations:
service registration, dependency management, multi-hop traversal,
blast radius calculation, and graph health checks.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.logging import get_logger
from app.graph.manager import KnowledgeGraphManager
from app.schemas.graph import (
    BlastRadiusResponse,
    DependencyCreate,
    DependencyResponse,
    GraphHealthResponse,
    ServiceCreate,
    ServiceDependenciesResponse,
    ServiceDetailResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


def get_graph_manager() -> KnowledgeGraphManager:
    """Dependency provider for KnowledgeGraphManager singleton."""
    return KnowledgeGraphManager()


@router.post(
    "/services",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register or update a microservice node",
)
async def register_service(
    payload: ServiceCreate,
    manager: KnowledgeGraphManager = Depends(get_graph_manager),
) -> dict:
    """
    Idempotently creates or updates a microservice node in the Neo4j Knowledge Graph.
    """
    try:
        service = manager.register_service(
            name=payload.name,
            environment=payload.environment,
            tier=payload.tier,
            team=payload.team,
            status=payload.status,
            metadata=payload.metadata,
        )
        return {
            "message": f"Service '{payload.name}' registered successfully.",
            "service": service,
        }
    except Exception as exc:
        logger.error("Failed to register service [%s]: %s", payload.name, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register service in graph: {str(exc)}",
        )


@router.post(
    "/dependencies",
    response_model=DependencyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a directed dependency relationship",
)
async def register_dependency(
    payload: DependencyCreate,
    manager: KnowledgeGraphManager = Depends(get_graph_manager),
) -> DependencyResponse:
    """
    Idempotently creates a directed relationship between two graph entities.
    Examples:
    - Service DEPENDS_ON Service
    - Service CONNECTS_TO Database
    - Service CALLS API
    - Service BELONGS_TO Repository
    """
    try:
        dep = manager.register_dependency(
            source=payload.source,
            target=payload.target,
            relation_type=payload.relation_type,
            source_type=payload.source_type,
            target_type=payload.target_type,
            properties=payload.properties,
        )
        return DependencyResponse(
            source=dep.get("source", payload.source),
            target=dep.get("target", payload.target),
            relation_type=dep.get("relation_type", payload.relation_type),
            source_type=payload.source_type,
            target_type=payload.target_type,
            properties=payload.properties,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error("Failed to register dependency [%s -> %s]: %s", payload.source, payload.target, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register dependency in graph: {str(exc)}",
        )


@router.get(
    "/services/{service_name}",
    response_model=ServiceDetailResponse,
    summary="Get microservice details and direct connections",
)
async def get_service(
    service_name: str,
    manager: KnowledgeGraphManager = Depends(get_graph_manager),
) -> ServiceDetailResponse:
    """
    Retrieves a microservice node with its direct callers, callees,
    databases, APIs, and associated source repositories.
    """
    svc = manager.get_service(service_name)
    if not svc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found in knowledge graph.",
        )

    return ServiceDetailResponse(
        name=svc["name"],
        environment=svc.get("environment", "production"),
        tier=svc.get("tier"),
        team=svc.get("team"),
        status=svc.get("status", "active"),
        metadata=svc.get("metadata", {}),
        upstream_dependencies=svc.get("upstream_dependencies", []),
        downstream_dependencies=svc.get("downstream_dependencies", []),
        connected_databases=svc.get("connected_databases", []),
        connected_apis=svc.get("connected_apis", []),
        repositories=svc.get("repositories", []),
    )


@router.get(
    "/services/{service_name}/dependencies",
    response_model=ServiceDependenciesResponse,
    summary="Get multi-hop dependencies for a service",
)
async def get_service_dependencies(
    service_name: str,
    direction: str = Query(default="both", pattern="^(upstream|downstream|both)$"),
    max_depth: int = Query(default=2, ge=1, le=5),
    manager: KnowledgeGraphManager = Depends(get_graph_manager),
) -> ServiceDependenciesResponse:
    """
    Traverses dependency graphs up to max_depth hops.
    - upstream: Services that depend on this service.
    - downstream: Services that this service depends on.
    - both: Full upstream and downstream topology.
    """
    deps = manager.get_service_dependencies(
        service_name=service_name,
        direction=direction,
        max_depth=max_depth,
    )
    return ServiceDependenciesResponse(
        service_name=service_name,
        direction=direction,
        max_depth=deps.get("max_depth", max_depth),
        upstream=deps.get("upstream", []),
        downstream=deps.get("downstream", []),
        databases=deps.get("databases", []),
        apis=deps.get("apis", []),
        traversal_paths=deps.get("traversal_paths", []),
    )


@router.get(
    "/services/{service_name}/blast-radius",
    response_model=BlastRadiusResponse,
    summary="Calculate failure blast radius and cascade impact",
)
async def get_service_blast_radius(
    service_name: str,
    max_depth: int = Query(default=3, ge=1, le=5),
    manager: KnowledgeGraphManager = Depends(get_graph_manager),
) -> BlastRadiusResponse:
    """
    Calculates the blast radius if the specified service fails, assessing
    immediate dependents, transitive cascade chains, affected databases,
    and computing a normalized impact score (0.0 to 1.0).
    """
    radius = manager.calculate_blast_radius(service_name=service_name, max_depth=max_depth)
    return BlastRadiusResponse(
        service_name=radius["service_name"],
        blast_radius_score=radius["blast_radius_score"],
        severity_level=radius["severity_level"],
        direct_dependents_count=radius["direct_dependents_count"],
        total_impacted_services_count=radius["total_impacted_services_count"],
        impacted_services=radius["impacted_services"],
        impacted_databases=radius["impacted_databases"],
        impacted_apis=radius["impacted_apis"],
        dependency_chains=radius["dependency_chains"],
    )


@router.get(
    "/health",
    response_model=GraphHealthResponse,
    summary="Neo4j Knowledge Graph connectivity and health check",
)
async def get_graph_health(
    manager: KnowledgeGraphManager = Depends(get_graph_manager),
) -> GraphHealthResponse:
    """
    Verifies Bolt protocol connection to Neo4j and returns node counts.
    """
    health = manager.health_check()
    return GraphHealthResponse(
        status=health["status"],
        connected=health["connected"],
        uri=health["uri"],
        database=health["database"],
        node_counts=health.get("node_counts"),
        error=health.get("error"),
    )
