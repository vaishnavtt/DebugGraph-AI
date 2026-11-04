"""
Reusable Pydantic response schemas for DebugGraph AI.
Standardizes health, readiness, generic API, and error envelopes.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


def current_utc_time() -> datetime:
    """Helper to return current UTC datetime."""
    return datetime.now(timezone.utc)


class HealthResponse(BaseModel):
    """Payload returned by the liveness/health endpoint."""

    status: str = Field(..., description="Overall service status (e.g., healthy)")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Semantic version string")
    environment: str = Field(..., description="Active runtime environment")
    timestamp: datetime = Field(default_factory=current_utc_time, description="UTC response timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "app_name": "DebugGraph AI",
                "version": "0.1.0",
                "environment": "development",
                "timestamp": "2026-11-01T00:00:00Z",
            }
        }
    )


class ReadinessResponse(BaseModel):
    """Payload returned by the dependency readiness endpoint."""

    status: str = Field(..., description="Overall readiness status (ready or not_ready)")
    services: Dict[str, str] = Field(
        default_factory=dict,
        description="Health and availability status per configured external service",
    )
    timestamp: datetime = Field(default_factory=current_utc_time, description="UTC response timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ready",
                "services": {
                    "database": "connected",
                    "neo4j": "reachable",
                    "qdrant": "connected",
                },
                "timestamp": "2026-11-01T00:00:00Z",
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standardized error response envelope."""

    error: bool = Field(default=True, description="Indicates error state")
    code: str = Field(..., description="Machine-readable error classification code")
    message: str = Field(..., description="Human-readable summary of the error")
    details: Optional[Any] = Field(
        default=None,
        description="Detailed contextual metadata, validation errors, or hints",
    )
    timestamp: datetime = Field(default_factory=current_utc_time, description="UTC timestamp of the error")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": True,
                "code": "NOT_FOUND",
                "message": "The requested resource could not be found.",
                "details": None,
                "timestamp": "2026-11-01T00:00:00Z",
            }
        }
    )


class APIResponse(BaseModel, Generic[T]):
    """Generic wrapper for standard successful API payloads."""

    success: bool = Field(default=True, description="Indicates operational success")
    data: Optional[T] = Field(default=None, description="Enclosed payload data")
    message: Optional[str] = Field(default=None, description="Optional informational message")
    timestamp: datetime = Field(default_factory=current_utc_time, description="UTC timestamp of the response")

