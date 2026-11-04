"""
Pydantic schemas for Neo4j Knowledge Graph entities, dependencies,
blast radius calculations, and health status.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ServiceCreate(BaseModel):
    """Schema for registering or updating a microservice node."""

    name: str = Field(..., min_length=1, description="Unique microservice name (e.g. 'payment-service')")
    environment: str = Field(default="production", description="Environment: 'production', 'staging', 'development'")
    tier: Optional[str] = Field(default=None, description="Architecture tier (e.g. 'frontend', 'backend', 'core')")
    team: Optional[str] = Field(default=None, description="Owning team (e.g. 'payments-team', 'platform')")
    status: str = Field(default="active", description="Service status: 'active', 'degraded', 'offline'")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary service metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "payment-service",
                "environment": "production",
                "tier": "backend",
                "team": "payments-core",
                "status": "active",
                "metadata": {"framework": "FastAPI", "version": "1.4.2"},
            }
        }
    )


class DatabaseCreate(BaseModel):
    """Schema for registering a database node."""

    name: str = Field(..., min_length=1, description="Unique database identifier (e.g. 'payments-db')")
    type: str = Field(default="postgresql", description="Database engine type (e.g. 'postgresql', 'redis', 'mongodb')")
    host: Optional[str] = Field(default=None, description="Database host or cluster endpoint")
    port: Optional[int] = Field(default=None, description="Database port number")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary database metadata")


class APICreate(BaseModel):
    """Schema for registering an API endpoint node."""

    name: str = Field(..., min_length=1, description="Unique API identifier (e.g. 'POST /api/v1/charge')")
    endpoint: Optional[str] = Field(default=None, description="API path (e.g. '/api/v1/charge')")
    method: str = Field(default="GET", description="HTTP method (e.g. 'GET', 'POST', 'PUT')")
    protocol: str = Field(default="HTTP", description="Protocol: 'HTTP', 'gRPC', 'GraphQL'")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary API metadata")


class DependencyCreate(BaseModel):
    """Schema for creating a directed relationship between two entities."""

    source: str = Field(..., min_length=1, description="Source entity identifier (e.g. 'checkout-service')")
    target: str = Field(..., min_length=1, description="Target entity identifier (e.g. 'payment-service')")
    relation_type: str = Field(
        default="DEPENDS_ON",
        description="Relationship type: 'DEPENDS_ON', 'CALLS', 'CONNECTS_TO', 'PRODUCES_ERROR', 'AFFECTED_BY', 'DEPLOYED_WITH', 'MODIFIED_BY', 'BELONGS_TO'",
    )
    source_type: str = Field(default="Service", description="Source node label (e.g. 'Service', 'Repository')")
    target_type: str = Field(default="Service", description="Target node label (e.g. 'Service', 'Database', 'API')")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relationship properties (e.g. 'timeout_ms')")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "checkout-service",
                "target": "payment-service",
                "relation_type": "DEPENDS_ON",
                "source_type": "Service",
                "target_type": "Service",
                "properties": {"critical": True, "timeout_ms": 3000},
            }
        }
    )


class DependencyResponse(BaseModel):
    """Response schema for an entity relationship."""

    source: str
    target: str
    relation_type: str
    source_type: str
    target_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class ServiceDetailResponse(BaseModel):
    """Detailed view of a microservice including connected entities."""

    name: str
    environment: str
    tier: Optional[str] = None
    team: Optional[str] = None
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    upstream_dependencies: List[str] = Field(
        default_factory=list,
        description="Services that depend on this service (callers)",
    )
    downstream_dependencies: List[str] = Field(
        default_factory=list,
        description="Services this service depends on (callees)",
    )
    connected_databases: List[str] = Field(
        default_factory=list,
        description="Databases this service connects to",
    )
    connected_apis: List[str] = Field(
        default_factory=list,
        description="APIs called by this service",
    )
    repositories: List[str] = Field(
        default_factory=list,
        description="Source code repositories linked to this service",
    )


class ServiceDependenciesResponse(BaseModel):
    """Multi-hop dependencies response for a service."""

    service_name: str
    direction: str = Field(..., description="'upstream', 'downstream', or 'both'")
    max_depth: int
    upstream: List[str] = Field(default_factory=list, description="Services depending on this service")
    downstream: List[str] = Field(default_factory=list, description="Services this service depends on")
    databases: List[str] = Field(default_factory=list, description="Databases connected in dependency path")
    apis: List[str] = Field(default_factory=list, description="APIs called in dependency path")
    traversal_paths: List[List[str]] = Field(default_factory=list, description="Traversed entity paths")


class BlastRadiusResponse(BaseModel):
    """Blast radius and cascade failure impact analysis for a microservice."""

    service_name: str
    blast_radius_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized impact score from 0.0 (isolated) to 1.0 (system-wide critical)",
    )
    severity_level: str = Field(
        ...,
        description="'CRITICAL', 'HIGH', 'MEDIUM', or 'LOW' based on blast radius score",
    )
    direct_dependents_count: int = Field(..., description="Number of immediate callers")
    total_impacted_services_count: int = Field(..., description="Total upstream & downstream services in cascade")
    impacted_services: List[str] = Field(default_factory=list, description="All potentially impacted microservices")
    impacted_databases: List[str] = Field(default_factory=list, description="All connected databases")
    impacted_apis: List[str] = Field(default_factory=list, description="All affected API endpoints")
    dependency_chains: List[List[str]] = Field(default_factory=list, description="Paths showing cascade propagation")


class GraphHealthResponse(BaseModel):
    """Health check response for the Neo4j Knowledge Graph."""

    status: str = Field(..., description="'healthy', 'degraded', or 'unavailable'")
    connected: bool = Field(..., description="Whether a Bolt session could be established")
    uri: str = Field(..., description="Neo4j connection URI")
    database: str = Field(..., description="Active Neo4j database name")
    node_counts: Optional[Dict[str, int]] = Field(default=None, description="Summary counts of graph nodes")
    error: Optional[str] = Field(default=None, description="Connection error message if unavailable")

