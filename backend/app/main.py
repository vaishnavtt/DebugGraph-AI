"""
DebugGraph AI - FastAPI Application Entry Point
Agentic RAG-Based Production Incident Investigation and Root Cause Analysis Platform
"""
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.api.health import get_health, get_readiness
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.database.session import init_db
from app.schemas.responses import HealthResponse, ReadinessResponse

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management for initialization and graceful shutdown."""
    # --- Startup Lifecycle ---
    setup_logging(settings.LOG_LEVEL)
    init_db()
    logger.info(
        "Starting %s (v%s) [DEBUG=%s, ENV_PREFIX=%s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.DEBUG,
        settings.API_V1_PREFIX,
    )

    yield

    # --- Shutdown Lifecycle ---
    logger.info("Shutting down %s cleanly.", settings.APP_NAME)


def create_application() -> FastAPI:
    """Factory function configuring and assembling the FastAPI application."""
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "DebugGraph AI - Agentic RAG-Based Production Incident Investigation "
            "and Root Cause Analysis Platform."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure Cross-Origin Resource Sharing (CORS)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register centralized exception handlers
    register_exception_handlers(application)

    # Register versioned API routes
    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Root endpoint
    @application.get(
        "/",
        tags=["General"],
        summary="Root Status",
        description="Root entry point providing basic API metadata and navigation links.",
    )
    async def root() -> Dict[str, Any]:
        return {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "online",
            "docs_url": "/docs",
            "health_url": f"{settings.API_V1_PREFIX}/health",
            "readiness_url": f"{settings.API_V1_PREFIX}/health/ready",
        }

    # Direct top-level health shortcuts
    @application.get(
        "/health",
        response_model=HealthResponse,
        tags=["Health"],
        summary="Application Liveness (Top-level alias)",
    )
    async def top_level_health() -> HealthResponse:
        return await get_health()

    @application.get(
        "/health/ready",
        response_model=ReadinessResponse,
        tags=["Health"],
        summary="Dependency Readiness (Top-level alias)",
    )
    async def top_level_readiness(response: Response) -> ReadinessResponse:
        return await get_readiness(response)

    return application


# Global FastAPI instance
app = create_application()
