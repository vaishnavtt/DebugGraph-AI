"""
Hybrid Retrieval and Reranking Engine for DebugGraph AI.
Coordinates dense semantic retrieval (Qdrant), sparse keyword retrieval (BM25),
Reciprocal Rank Fusion (RRF), and Cross-Encoder reranking (BGE Reranker)
to produce evidence-grounded incident log chunks.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.retrieval.bm25_search import BM25SearchService
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.fusion import FusedCandidate, reciprocal_rank_fusion
from app.retrieval.reranker import CrossEncoderReranker
from app.retrieval.vector_store import QdrantVectorStore

logger = get_logger(__name__)


@dataclass
class RetrievalDiagnostics:
    """Detailed diagnostics explaining how a log chunk was retrieved and scored."""

    chunk_id: str
    retrieval_methods: List[str]
    dense_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    dense_score: Optional[float] = None
    bm25_score: Optional[float] = None
    rrf_score: float = 0.0
    reranker_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "retrieval_methods": self.retrieval_methods,
            "dense_rank": self.dense_rank,
            "bm25_rank": self.bm25_rank,
            "dense_score": self.dense_score,
            "bm25_score": self.bm25_score,
            "rrf_score": self.rrf_score,
            "reranker_score": self.reranker_score,
        }


@dataclass
class HybridSearchResult:
    """Final retrieved evidence item returned by the hybrid engine."""

    chunk_id: str
    content: str
    original_filename: str
    service_name: Optional[str]
    severity: Optional[str]
    timestamp_start: Optional[str]
    timestamp_end: Optional[str]
    source_line_start: int
    source_line_end: int
    source_entry_ids: List[str]
    exception_signatures: List[str]
    dense_score: Optional[float]
    bm25_score: Optional[float]
    rrf_score: float
    reranker_score: Optional[float]
    diagnostics: RetrievalDiagnostics
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "relevant_log_content": self.content,
            "original_filename": self.original_filename,
            "service_name": self.service_name,
            "severity": self.severity,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "source_line_start": self.source_line_start,
            "source_line_end": self.source_line_end,
            "source_entry_ids": self.source_entry_ids,
            "exception_signatures": self.exception_signatures,
            "dense_score": self.dense_score,
            "bm25_score": self.bm25_score,
            "rrf_score": self.rrf_score,
            "reranker_score": self.reranker_score,
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": self.metadata,
        }


class HybridSearchEngine:
    """
    Coordinates multi-stage retrieval:
    1. Dense Vector Search (Qdrant)
    2. BM25 Keyword Search
    3. Reciprocal Rank Fusion (RRF)
    4. Cross-Encoder Reranking (BGE-Reranker)
    """

    def __init__(
        self,
        vector_store: Optional[QdrantVectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
        bm25_service: Optional[BM25SearchService] = None,
        reranker: Optional[CrossEncoderReranker] = None,
    ) -> None:
        self.vector_store = vector_store or QdrantVectorStore()
        self.embedding_service = embedding_service or EmbeddingService.get_instance()
        self.bm25_service = bm25_service or BM25SearchService.get_instance()
        self.reranker = reranker or CrossEncoderReranker.get_instance()

    def search(
        self,
        query: str,
        top_k: int = 5,
        service_name: Optional[str] = None,
        severity: Optional[str] = None,
        ingestion_id: Optional[str] = None,
        candidate_k: Optional[int] = None,
        rerank: bool = True,
    ) -> List[HybridSearchResult]:
        """
        Executes end-to-end hybrid retrieval and reranking for a query.

        Parameters:
        - query: Search query (natural language or technical identifier/error code).
        - top_k: Final number of ranked results to return.
        - service_name: Optional service filter.
        - severity: Optional log severity filter (e.g. 'ERROR').
        - ingestion_id: Optional filter for specific ingestion upload.
        - candidate_k: Number of candidates retrieved from dense and sparse stages (default 20).
        - rerank: Whether to execute cross-encoder reranking.
        """
        stripped_query = query.strip()
        if not stripped_query:
            return []

        candidates_limit = candidate_k or settings.HYBRID_RETRIEVAL_CANDIDATE_K

        # ---------------------------------------------------------
        # Stage 1: Dense Semantic Vector Retrieval (Qdrant)
        # ---------------------------------------------------------
        dense_results: List[Dict[str, Any]] = []
        try:
            query_vector = self.embedding_service.embed_query(stripped_query)
            dense_results = self.vector_store.search(
                query_vector=query_vector,
                top_k=candidates_limit,
                service_name=service_name,
                severity=severity,
                ingestion_id=ingestion_id,
            )
            logger.debug("Dense retrieval returned %d candidates.", len(dense_results))
        except Exception as exc:
            logger.warning("Dense vector retrieval failed: %s. Continuing with BM25 only.", exc)

        # ---------------------------------------------------------
        # Stage 2: Sparse BM25 Keyword Retrieval
        # ---------------------------------------------------------
        sparse_results: List[Dict[str, Any]] = []
        try:
            sparse_results = self.bm25_service.search(
                query=stripped_query,
                top_k=candidates_limit,
                service_name=service_name,
                severity=severity,
                ingestion_id=ingestion_id,
            )
            logger.debug("BM25 retrieval returned %d candidates.", len(sparse_results))
        except Exception as exc:
            logger.warning("BM25 retrieval failed: %s. Continuing with dense only.", exc)

        if not dense_results and not sparse_results:
            logger.info("Neither dense nor sparse retrieval returned results for query: '%s'", stripped_query)
            return []

        # ---------------------------------------------------------
        # Stage 3: Reciprocal Rank Fusion (RRF)
        # ---------------------------------------------------------
        fused_candidates: List[FusedCandidate] = reciprocal_rank_fusion(
            dense_results=dense_results,
            sparse_results=sparse_results,
            k=settings.RRF_K,
        )

        if not fused_candidates:
            return []

        # Slice candidate pool for reranker (e.g. top candidates_limit)
        rerank_pool = fused_candidates[:candidates_limit]

        # ---------------------------------------------------------
        # Stage 4: Cross-Encoder Reranking
        # ---------------------------------------------------------
        if rerank:
            ranked_dicts = self.reranker.rerank(
                query=stripped_query,
                candidates=rerank_pool,
                top_k=top_k,
            )
        else:
            ranked_dicts = [c.to_dict() for c in rerank_pool[:top_k]]

        # ---------------------------------------------------------
        # Stage 5: Package Final Evidence & Diagnostics
        # ---------------------------------------------------------
        final_results: List[HybridSearchResult] = []
        for item in ranked_dicts:
            chunk_id = item.get("chunk_id", "")
            diagnostics = RetrievalDiagnostics(
                chunk_id=chunk_id,
                retrieval_methods=item.get("retrieval_methods", []),
                dense_rank=item.get("dense_rank"),
                bm25_rank=item.get("bm25_rank"),
                dense_score=item.get("dense_score"),
                bm25_score=item.get("bm25_score"),
                rrf_score=item.get("rrf_score", 0.0),
                reranker_score=item.get("reranker_score"),
            )

            final_results.append(
                HybridSearchResult(
                    chunk_id=chunk_id,
                    content=item.get("content") or item.get("relevant_log_content") or "",
                    original_filename=item.get("original_filename", ""),
                    service_name=item.get("service_name"),
                    severity=item.get("severity"),
                    timestamp_start=item.get("timestamp_start"),
                    timestamp_end=item.get("timestamp_end"),
                    source_line_start=item.get("source_line_start", 0),
                    source_line_end=item.get("source_line_end", 0),
                    source_entry_ids=item.get("source_entry_ids", []),
                    exception_signatures=item.get("exception_signatures", []),
                    dense_score=item.get("dense_score"),
                    bm25_score=item.get("bm25_score"),
                    rrf_score=item.get("rrf_score", 0.0),
                    reranker_score=item.get("reranker_score"),
                    diagnostics=diagnostics,
                    metadata=item.get("metadata", {}),
                )
            )

        return final_results

