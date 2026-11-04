"""
Search API endpoints for DebugGraph AI.
Provides hybrid retrieval and reranking combining vector embeddings, BM25, and cross-encoders.
"""
from fastapi import APIRouter, status

from app.core.logging import get_logger
from app.retrieval.hybrid_search import HybridSearchEngine, HybridSearchResult
from app.schemas.search import (
    HybridSearchRequest,
    HybridSearchResponse,
    HybridSearchResultHit,
    RetrievalDiagnosticsSchema,
)

logger = get_logger(__name__)
router = APIRouter(tags=["Retrieval & Search"])
hybrid_engine = HybridSearchEngine()


@router.post(
    "/search/hybrid",
    response_model=HybridSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Hybrid Retrieval and Reranking Search",
    description=(
        "Executes multi-stage hybrid retrieval combining Qdrant dense vector search, "
        "BM25 keyword search, Reciprocal Rank Fusion (RRF), and BGE Cross-Encoder reranking."
    ),
)
def hybrid_search(
    request: HybridSearchRequest,
) -> HybridSearchResponse:
    """Execute hybrid retrieval pipeline and return evidence log chunks with diagnostics."""
    logger.info("Executing hybrid search for query: '%s'", request.query)

    results: list[HybridSearchResult] = hybrid_engine.search(
        query=request.query,
        top_k=request.top_k,
        service_name=request.service_name,
        severity=request.severity,
        ingestion_id=request.ingestion_id,
        rerank=request.rerank,
    )

    hits: list[HybridSearchResultHit] = []
    for r in results:
        hits.append(
            HybridSearchResultHit(
                chunk_id=r.chunk_id,
                content=r.content,
                dense_score=r.dense_score,
                bm25_score=r.bm25_score,
                rrf_score=r.rrf_score,
                reranker_score=r.reranker_score,
                original_filename=r.original_filename,
                service_name=r.service_name,
                severity=r.severity,
                timestamp_start=r.timestamp_start,
                timestamp_end=r.timestamp_end,
                source_line_start=r.source_line_start,
                source_line_end=r.source_line_end,
                source_entry_ids=r.source_entry_ids,
                exception_signatures=r.exception_signatures,
                diagnostics=RetrievalDiagnosticsSchema(
                    chunk_id=r.diagnostics.chunk_id,
                    retrieval_methods=r.diagnostics.retrieval_methods,
                    dense_rank=r.diagnostics.dense_rank,
                    bm25_rank=r.diagnostics.bm25_rank,
                    dense_score=r.diagnostics.dense_score,
                    bm25_score=r.diagnostics.bm25_score,
                    rrf_score=r.diagnostics.rrf_score,
                    reranker_score=r.diagnostics.reranker_score,
                ),
                metadata=r.metadata,
            )
        )

    return HybridSearchResponse(
        query=request.query,
        total_results=len(hits),
        results=hits,
    )

