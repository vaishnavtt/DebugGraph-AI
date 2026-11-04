"""
Unit tests for Qdrant vector store integration.
Validates collection lifecycle, vector insertion, idempotent deletion, and metadata filtering.
Uses in-memory Qdrant client for isolated execution without external server dependency.
"""
import pytest
from qdrant_client import QdrantClient

from app.retrieval.chunking import LogChunk
from app.retrieval.vector_store import QdrantVectorStore


@pytest.fixture
def in_memory_vector_store() -> QdrantVectorStore:
    """Fixture providing a fresh in-memory QdrantVectorStore instance."""
    mem_client = QdrantClient(":memory:")
    store = QdrantVectorStore(collection_name="test_debuggraph_logs", client=mem_client)
    store.ensure_collection()
    return store


def test_qdrant_collection_initialization(in_memory_vector_store: QdrantVectorStore) -> None:
    """Validate collection is created with expected configuration and cosine similarity."""
    info = in_memory_vector_store.get_collection_info()
    assert info["collection_name"] == "test_debuggraph_logs"
    assert info["vector_size"] == 384
    assert "Cosine" in info["distance"] or "cosine" in info["distance"].lower()


def test_vector_insertion_and_search(in_memory_vector_store: QdrantVectorStore) -> None:
    """Validate inserting chunks and performing similarity search."""
    # Synthetic 384-dimensional vectors
    v1 = [0.1] * 384
    v2 = [-0.1] * 384

    c1 = LogChunk(
        chunk_id="c_1",
        ingestion_id="ingest_1",
        chunk_index=0,
        content="Payment service gateway timeout",
        service_name="payment-service",
        source_line_start=1,
        source_line_end=5,
        original_filename="payment.log",
        metadata={
            "chunk_id": "c_1",
            "ingestion_id": "ingest_1",
            "service_name": "payment-service",
            "severity": "ERROR",
            "original_filename": "payment.log",
            "content": "Payment service gateway timeout",
            "source_line_start": 1,
            "source_line_end": 5,
        },
    )

    c2 = LogChunk(
        chunk_id="c_2",
        ingestion_id="ingest_1",
        chunk_index=1,
        content="User authentication successful",
        service_name="auth-service",
        source_line_start=6,
        source_line_end=8,
        original_filename="payment.log",
        metadata={
            "chunk_id": "c_2",
            "ingestion_id": "ingest_1",
            "service_name": "auth-service",
            "severity": "INFO",
            "original_filename": "payment.log",
            "content": "User authentication successful",
            "source_line_start": 6,
            "source_line_end": 8,
        },
    )

    count = in_memory_vector_store.insert_vectors([c1, c2], [v1, v2])
    assert count == 2

    # Query vector close to v1
    query_vec = [0.1] * 384
    results = in_memory_vector_store.search(query_vector=query_vec, top_k=2)
    assert len(results) == 2
    assert results[0]["chunk_id"] == "c_1"
    assert results[0]["similarity_score"] > 0.95


def test_metadata_filtering(in_memory_vector_store: QdrantVectorStore) -> None:
    """Validate metadata filtering by service_name and severity."""
    v1 = [0.1] * 384
    v2 = [0.1] * 384

    c1 = LogChunk(
        chunk_id="chunk_err",
        ingestion_id="ing_filter",
        chunk_index=0,
        content="Error log in payment service",
        service_name="payment-service",
        source_line_start=1,
        source_line_end=2,
        original_filename="app.log",
        metadata={
            "chunk_id": "chunk_err",
            "ingestion_id": "ing_filter",
            "service_name": "payment-service",
            "severity": "ERROR",
            "content": "Error log in payment service",
            "source_line_start": 1,
            "source_line_end": 2,
        },
    )
    c2 = LogChunk(
        chunk_id="chunk_info",
        ingestion_id="ing_filter",
        chunk_index=1,
        content="Info log in auth service",
        service_name="auth-service",
        source_line_start=3,
        source_line_end=4,
        original_filename="app.log",
        metadata={
            "chunk_id": "chunk_info",
            "ingestion_id": "ing_filter",
            "service_name": "auth-service",
            "severity": "INFO",
            "content": "Info log in auth service",
            "source_line_start": 3,
            "source_line_end": 4,
        },
    )

    in_memory_vector_store.insert_vectors([c1, c2], [v1, v2])

    # Filter by service_name
    hits_payment = in_memory_vector_store.search(
        query_vector=v1, top_k=5, service_name="payment-service"
    )
    assert len(hits_payment) == 1
    assert hits_payment[0]["chunk_id"] == "chunk_err"

    # Filter by severity
    hits_error = in_memory_vector_store.search(query_vector=v1, top_k=5, severity="ERROR")
    assert len(hits_error) == 1
    assert hits_error[0]["chunk_id"] == "chunk_err"


def test_duplicate_indexing_prevention(in_memory_vector_store: QdrantVectorStore) -> None:
    """Validate delete_by_ingestion_id purges previous vectors before re-indexing."""
    v = [0.2] * 384
    c = LogChunk(
        chunk_id="chunk_dup",
        ingestion_id="ing_dup_1",
        chunk_index=0,
        content="Duplicate test log",
        service_name="db-service",
        source_line_start=1,
        source_line_end=1,
        original_filename="db.log",
        metadata={
            "chunk_id": "chunk_dup",
            "ingestion_id": "ing_dup_1",
            "service_name": "db-service",
            "severity": "INFO",
            "content": "Duplicate test log",
            "source_line_start": 1,
            "source_line_end": 1,
        },
    )

    in_memory_vector_store.insert_vectors([c], [v])
    hits_before = in_memory_vector_store.search(query_vector=v, top_k=5, ingestion_id="ing_dup_1")
    assert len(hits_before) == 1

    # Purge
    in_memory_vector_store.delete_by_ingestion_id("ing_dup_1")
    hits_after = in_memory_vector_store.search(query_vector=v, top_k=5, ingestion_id="ing_dup_1")
    assert len(hits_after) == 0

