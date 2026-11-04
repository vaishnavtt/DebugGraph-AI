"""
Pydantic schemas for vector indexing and semantic search operations.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class IndexingResponse(BaseModel):
    """Result returned upon completing vector indexing of an ingestion."""

    ingestion_id: str = Field(..., description="Unique ingestion identifier")
    status: str = Field(..., description="Indexing state (e.g., indexed)")
    indexed_chunks: int = Field(..., description="Total vector chunks generated and indexed in Qdrant")
    total_log_entries: int = Field(..., description="Total underlying log entries included")
    original_filename: str = Field(..., description="Source log file name")
    vector_dimension: int = Field(..., description="Embedding vector size (e.g., 384)")
    collection_name: str = Field(..., description="Target Qdrant collection name")
    message: str = Field(..., description="Status explanation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ingestion_id": "ingest_a1b2c3d4",
                "status": "indexed",
                "indexed_chunks": 4,
                "total_log_entries": 12,
                "original_filename": "payment-service.log",
                "vector_dimension": 384,
                "collection_name": "debuggraph_logs",
                "message": "Successfully indexed 4 chunks from 12 log entries.",
            }
        }
    )


class IndexingStatusResponse(BaseModel):
    """Current vector indexing progress and status for an ingestion."""

    ingestion_id: str = Field(..., description="Ingestion run identifier")
    status: str = Field(..., description="Current status: pending, indexing, indexed, or failed")
    indexed_chunks_count: int = Field(..., description="Number of chunks currently stored in Qdrant")
    total_entries: int = Field(..., description="Total parsed log entries available")
    filename: str = Field(..., description="Uploaded log file name")
    created_at: datetime = Field(..., description="Ingestion creation timestamp")
    updated_at: datetime = Field(..., description="Last updated timestamp")


class SemanticSearchRequest(BaseModel):
    """Parameters for executing a semantic vector search query."""

    query: str = Field(..., min_length=1, description="Natural language search query or error description")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of relevant chunks to retrieve")
    service_name: Optional[str] = Field(default=None, description="Filter results to a specific service")
    severity: Optional[str] = Field(default=None, description="Filter results to a specific severity level")
    ingestion_id: Optional[str] = Field(default=None, description="Filter results to a specific ingestion job")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Database connection pool timeout during checkout",
                "top_k": 3,
                "service_name": "payment-service",
                "severity": "ERROR",
                "ingestion_id": None,
            }
        }
    )


class SearchResultHit(BaseModel):
    """Individual retrieved log chunk hit with relevance score and location references."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    original_filename: str = Field(..., description="Source log file name")
    relevant_log_content: str = Field(..., description="Text content of the retrieved chunk")
    service_name: Optional[str] = Field(default=None, description="Associated service name")
    timestamp_start: Optional[str] = Field(default=None, description="Earliest timestamp in chunk")
    timestamp_end: Optional[str] = Field(default=None, description="Latest timestamp in chunk")
    severity: Optional[str] = Field(default=None, description="Dominant severity in chunk")
    source_line_start: int = Field(..., description="Starting line number in source log file")
    source_line_end: int = Field(..., description="Ending line number in source log file")
    source_entry_ids: List[str] = Field(default_factory=list, description="IDs of enclosed log records")
    exception_signatures: List[str] = Field(default_factory=list, description="Exceptions observed in chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Complete Qdrant payload attributes")


class SemanticSearchResponse(BaseModel):
    """Response containing retrieved log chunks ranked by semantic relevance."""

    query: str = Field(..., description="Original input query")
    total_hits: int = Field(..., description="Count of retrieved chunks")
    hits: List[SearchResultHit] = Field(default_factory=list, description="Ranked list of search results")

