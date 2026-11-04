"""
Integration tests for vector indexing service and semantic search endpoints.
Validates end-to-end flow:
1. File upload -> Database persistence
2. Persistence verification across simulated restarts
3. Vector indexing -> Qdrant storage
4. Idempotent re-indexing
5. Semantic vector search API
"""
import io
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import numpy as np
import pytest
from qdrant_client import QdrantClient

from app.api.indexing import indexing_service
from app.core.config import settings
from app.database.models import IngestionRecord, ParsedLogEntryModel
from app.database.session import get_db_context
from app.main import app
from app.retrieval.chunking import LogChunker
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import QdrantVectorStore
from app.services.vector_indexing_service import VectorIndexingService

client = TestClient(app)


@pytest.fixture
def test_indexing_env(monkeypatch: pytest.MonkeyPatch) -> QdrantVectorStore:
    """Configures in-memory vector store and deterministic embedding service."""
    mem_client = QdrantClient(":memory:")
    vector_store = QdrantVectorStore(collection_name="test_indexing_logs", client=mem_client)
    vector_store.ensure_collection()

    # Deterministic mock embedding service
    mock_embedder = MagicMock(spec=EmbeddingService)
    mock_embedder.expected_dim = 384
    mock_embedder.batch_size = 32

    def fake_embed_docs(texts):
        # Deterministic normalized 384-d vectors
        vecs = []
        for i, _ in enumerate(texts):
            v = np.zeros(384, dtype=np.float32)
            v[i % 384] = 1.0
            vecs.append(v.tolist())
        return vecs

    def fake_embed_query(query):
        v = np.zeros(384, dtype=np.float32)
        v[0] = 1.0
        return v.tolist()

    mock_embedder.embed_documents.side_effect = fake_embed_docs
    mock_embedder.embed_query.side_effect = fake_embed_query

    svc = VectorIndexingService(
        embedding_service=mock_embedder,
        vector_store=vector_store,
        chunker=LogChunker(max_entries_per_chunk=3, overlap_entries=1),
    )

    # Patch the global router indexing service
    monkeypatch.setattr("app.api.indexing.indexing_service", svc)

    return vector_store


def test_database_persistence_across_restart() -> None:
    """Verify that uploaded log entries persist in the database and can be retrieved."""
    log_content = (
        b"2026-11-01 10:15:01 INFO [order-service] Order received\n"
        b"2026-11-01 10:15:05 ERROR [order-service] Payment gateway timeout\n"
    )

    upload_resp = client.post(
        f"{settings.API_V1_PREFIX}/logs/upload",
        files={"file": ("persist_test.log", io.BytesIO(log_content), "text/plain")},
    )
    assert upload_resp.status_code == 201
    ingestion_id = upload_resp.json()["ingestion_id"]

    # Direct database query simulating retrieval after application restart
    with get_db_context() as db:
        record = db.query(IngestionRecord).filter(IngestionRecord.id == ingestion_id).first()
        assert record is not None
        assert record.filename == "persist_test.log"
        assert record.total_entries == 2

        entries = (
            db.query(ParsedLogEntryModel)
            .filter(ParsedLogEntryModel.ingestion_id == ingestion_id)
            .order_by(ParsedLogEntryModel.id.asc())
            .all()
        )
        assert len(entries) == 2
        assert entries[0].severity == "INFO"
        assert entries[1].severity == "ERROR"


def test_vector_indexing_and_search_flow(test_indexing_env: QdrantVectorStore) -> None:
    """End-to-end test of ingestion, vector indexing, status inquiry, and semantic search."""
    # 1. Upload sample log
    log_content = (
        b"2026-11-01 10:15:01 INFO [payment-service] Initializing payment worker\n"
        b"2026-11-01 10:15:05 ERROR [payment-service] Gateway connection timeout during checkout\n"
        b"Traceback (most recent call last):\n"
        b"  File '/app/pay.py', line 12, in pay\n"
        b"    raise TimeoutError('Stripe timeout')\n"
        b"TimeoutError: Stripe timeout\n"
        b"2026-11-01 10:15:10 CRITICAL [payment-service] Circuit breaker tripped for StripeClient\n"
    )

    upload_resp = client.post(
        f"{settings.API_V1_PREFIX}/logs/upload",
        files={"file": ("checkout.log", io.BytesIO(log_content), "text/plain")},
    )
    assert upload_resp.status_code == 201
    ingestion_id = upload_resp.json()["ingestion_id"]

    # 2. Trigger Vector Indexing
    index_resp = client.post(f"{settings.API_V1_PREFIX}/indexing/{ingestion_id}")
    assert index_resp.status_code == 200
    index_data = index_resp.json()
    assert index_data["status"] == "indexed"
    assert index_data["indexed_chunks"] > 0
    assert index_data["total_log_entries"] == 3

    # 3. Check Indexing Status
    status_resp = client.get(f"{settings.API_V1_PREFIX}/indexing/{ingestion_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "indexed"
    assert status_data["indexed_chunks_count"] == index_data["indexed_chunks"]

    # 4. Verify Idempotent Re-indexing (does not create duplicate vectors)
    reindex_resp = client.post(f"{settings.API_V1_PREFIX}/indexing/{ingestion_id}")
    assert reindex_resp.status_code == 200

    q_info = test_indexing_env.get_collection_info()
    # Total points should equal index_data["indexed_chunks"], not doubled!
    assert q_info["points_count"] == index_data["indexed_chunks"]

    # 5. Execute Semantic Search API
    search_payload = {
        "query": "gateway connection timeout",
        "top_k": 3,
        "service_name": "payment-service",
    }
    search_resp = client.post(f"{settings.API_V1_PREFIX}/search/semantic", json=search_payload)
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total_hits"] > 0

    hit = search_data["hits"][0]
    assert hit["original_filename"] == "checkout.log"
    assert hit["service_name"] == "payment-service"
    assert hit["source_line_start"] >= 1
    assert "content" in hit["relevant_log_content"].lower() or len(hit["relevant_log_content"]) > 0


def test_indexing_nonexistent_ingestion_fails(test_indexing_env: QdrantVectorStore) -> None:
    """Ensure indexing a non-existent ingestion returns 404."""
    resp = client.post(f"{settings.API_V1_PREFIX}/indexing/ingest_nonexistent_999")
    assert resp.status_code == 404
    data = resp.json()
    assert data["code"] == "INGESTION_NOT_FOUND"

