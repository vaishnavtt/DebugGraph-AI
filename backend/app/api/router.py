"""
Main API router aggregating all versioned endpoints for DebugGraph AI.
"""
from fastapi import APIRouter
from app.api.analysis import router as analysis_router
from app.api.evaluation import router as evaluation_router
from app.api.github import router as github_router
from app.api.graph import router as graph_router
from app.api.health import router as health_router
from app.api.indexing import router as indexing_router
from app.api.logs import router as logs_router
from app.api.search import router as search_router

api_router = APIRouter()

# Register health endpoints under the versioned prefix
api_router.include_router(health_router, tags=["Health"])

# Register log ingestion endpoints
api_router.include_router(logs_router)

# Register vector indexing endpoints
api_router.include_router(indexing_router)

# Register hybrid retrieval and search endpoints
api_router.include_router(search_router)

# Register incident analysis and Gemini LLM investigation endpoints
api_router.include_router(analysis_router)

# Register Neo4j Knowledge Graph endpoints
api_router.include_router(graph_router)

# Register GitHub Repository and Commit Intelligence endpoints
api_router.include_router(github_router)

# Register Evaluation and Benchmarking endpoints
api_router.include_router(evaluation_router)
