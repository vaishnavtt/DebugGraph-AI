"""
Vector Indexing and Semantic Search API Endpoints for DebugGraph AI.
"""
from fastapi import APIRouter, Path, status

from app.schemas.indexing import (
    IndexingResponse,
    IndexingStatusResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
)
from app.services.vector_indexing_service import VectorIndexingService

router = APIRouter(tags=["Vector Indexing & Search"])
indexing_service = VectorIndexingService()


@router.post(
    "/indexing/{ingestion_id}",
    response_model=IndexingResponse,
    status_code=status.HTTP_200_OK,
    summary="Start Vector Indexing for Ingestion",
    description="Loads persisted log entries for the ingestion ID, generates semantic chunks and embeddings, and indexes into Qdrant.",
)
def start_vector_indexing(
    ingestion_id: str = Path(..., description="Unique ingestion identifier to index"),
) -> IndexingResponse:
    """Index persisted log entries into Qdrant vector database."""
    return indexing_service.index_ingestion(ingestion_id)


@router.get(
    "/indexing/{ingestion_id}/status",
    response_model=IndexingStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Ingestion Indexing Status",
    description="Returns the current indexing state, chunk count, and metadata for an ingestion job.",
)
def get_indexing_status(
    ingestion_id: str = Path(..., description="Unique ingestion identifier to check"),
) -> IndexingStatusResponse:
    """Retrieve indexing status and progress."""
    return indexing_service.get_status(ingestion_id)


@router.post(
    "/search/semantic",
    response_model=SemanticSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic Vector Search",
    description="Performs semantic similarity retrieval against indexed log vectors in Qdrant with optional metadata filtering.",
)
def semantic_search(
    request: SemanticSearchRequest,
) -> SemanticSearchResponse:
    """Execute dense semantic search against Qdrant without LLM generation."""
    return indexing_service.search_semantic(request)

