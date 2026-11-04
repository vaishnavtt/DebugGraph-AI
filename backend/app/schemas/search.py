"""
Pydantic schemas for Hybrid Retrieval and Search API.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class HybridSearchRequest(BaseModel):
    """Request payload for executing hybrid search with RRF and cross-encoder reranking."""

    query: str = Field(..., min_length=1, description="Natural language incident query or technical error code")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of top evidence chunks to return")
    service_name: Optional[str] = Field(default=None, description="Filter results to a specific service")
    service: Optional[str] = Field(default=None, description="Alternative alias for service_name")
    severity: Optional[str] = Field(default=None, description="Filter results to a specific severity level")
    ingestion_id: Optional[str] = Field(default=None, description="Filter results to a specific ingestion job")
    rerank: bool = Field(default=True, description="Whether to execute cross-encoder reranking")

    @model_validator(mode="before")
    @classmethod
    def resolve_service_alias(cls, values: Any) -> Any:
        """Allow callers to pass either 'service' or 'service_name'."""
        if isinstance(values, dict):
            if "service_name" not in values and "service" in values:
                values["service_name"] = values["service"]
        return values

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Why are payment transactions failing with connection timeouts?",
                "top_k": 5,
                "service_name": "payment-service",
                "severity": "ERROR",
                "ingestion_id": None,
                "rerank": True,
            }
        }
    )


class RetrievalDiagnosticsSchema(BaseModel):
    """Detailed diagnostics explaining retrieval methods, ranks, and individual scores."""

    chunk_id: str = Field(..., description="Target chunk identifier")
    retrieval_methods: List[str] = Field(..., description="Methods that retrieved this chunk: ['dense', 'bm25']")
    dense_rank: Optional[int] = Field(default=None, description="1-based rank in dense vector retrieval")
    bm25_rank: Optional[int] = Field(default=None, description="1-based rank in BM25 keyword retrieval")
    dense_score: Optional[float] = Field(default=None, description="Dense cosine similarity score")
    bm25_score: Optional[float] = Field(default=None, description="Raw BM25Okapi relevance score")
    rrf_score: float = Field(..., description="Reciprocal Rank Fusion score (RRF(d) = SUM(1/(k + rank)))")
    reranker_score: Optional[float] = Field(
        default=None, description="Cross-encoder relevance logit (not a probability)"
    )


class HybridSearchResultHit(BaseModel):
    """Ranked evidence log chunk returned by the hybrid engine."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    content: str = Field(..., description="Enclosed log content of the chunk")
    dense_score: Optional[float] = Field(default=None, description="Cosine similarity score from vector search")
    bm25_score: Optional[float] = Field(default=None, description="Keyword relevance score from BM25")
    rrf_score: float = Field(..., description="Reciprocal Rank Fusion score")
    reranker_score: Optional[float] = Field(
        default=None, description="BGE cross-encoder relevance score (uncalibrated logit)"
    )
    original_filename: str = Field(default="", description="Source log file name")
    service_name: Optional[str] = Field(default=None, description="Associated service name")
    severity: Optional[str] = Field(default=None, description="Dominant severity in chunk")
    timestamp_start: Optional[str] = Field(default=None, description="Earliest timestamp in chunk")
    timestamp_end: Optional[str] = Field(default=None, description="Latest timestamp in chunk")
    source_line_start: int = Field(default=0, description="Starting line in source file")
    source_line_end: int = Field(default=0, description="Ending line in source file")
    source_entry_ids: List[str] = Field(default_factory=list, description="IDs of enclosed log records")
    exception_signatures: List[str] = Field(default_factory=list, description="Exceptions identified in chunk")
    diagnostics: RetrievalDiagnosticsSchema = Field(..., description="Retrieval source and ranking diagnostics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional chunk attributes")


class HybridSearchResponse(BaseModel):
    """Response containing hybrid-retrieved evidence chunks ranked by relevance."""

    query: str = Field(..., description="Original input query")
    total_results: int = Field(..., description="Count of retrieved evidence chunks")
    results: List[HybridSearchResultHit] = Field(default_factory=list, description="Ranked evidence results")

