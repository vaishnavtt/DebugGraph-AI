"""
Unit and integration tests for BM25 keyword retrieval and technical tokenization.
"""
from datetime import datetime, timezone
import json
import pytest

from app.database.models import IngestionRecord, LogChunkRecord
from app.database.session import get_db_context
from app.retrieval.bm25_search import BM25SearchService, tokenize_log_text


def test_technical_tokenization_preserves_identifiers():
    """Ensure technical tokens, error codes, and paths are retained and tokenized."""
    log_text = (
        "2026-11-01 10:15:00 ERROR [payment-service] HTTP 500 DB-1045: "
        "ConnectionTimeoutError in /app/payment/gateway.py for order_id=ord_9981"
    )
    tokens = tokenize_log_text(log_text)

    # 1. HTTP 500
    assert "http_500" in tokens
    assert "500" in tokens

    # 2. Hyphenated error codes and services
    assert "db-1045" in tokens
    assert "1045" in tokens
    assert "payment-service" in tokens
    assert "payment" in tokens
    assert "service" in tokens

    # 3. CamelCase exceptions
    assert "connectiontimeouterror" in tokens
    assert "connection" in tokens
    assert "timeout" in tokens

    # 4. Dotted filename and underscore identifiers
    assert "gateway.py" in tokens
    assert "ord_9981" in tokens


def test_empty_query_returns_empty_results():
    """Ensure empty or whitespace queries cleanly return an empty result set."""
    service = BM25SearchService()
    assert service.search("") == []
    assert service.search("   ") == []


def test_bm25_retrieval_and_exact_error_code_matching():
    """Verify BM25 indexes chunks from database, matches exact error codes, and ranks correctly."""
    ingestion_id = "ingest_test_bm25_1"

    with get_db_context() as db:
        # Clean up any existing records
        db.query(LogChunkRecord).filter(LogChunkRecord.ingestion_id == ingestion_id).delete()
        db.query(IngestionRecord).filter(IngestionRecord.id == ingestion_id).delete()

        # Insert parent ingestion record
        ing_rec = IngestionRecord(
            id=ingestion_id,
            filename="auth-service.log",
            file_size_bytes=1024,
            format_detected="text",
            total_entries=3,
            parsed_entries=3,
        )
        db.add(ing_rec)

        # Insert 3 test chunks
        chunk1 = LogChunkRecord(
            id=f"{ingestion_id}_chunk_0",
            ingestion_id=ingestion_id,
            chunk_index=0,
            service_name="auth-service",
            severities_json=json.dumps(["INFO"]),
            timestamp_start=datetime.now(timezone.utc),
            timestamp_end=datetime.now(timezone.utc),
            source_line_start=1,
            source_line_end=5,
            content="2026-11-01 10:00:00 INFO [auth-service] User session token refreshed successfully",
        )
        chunk2 = LogChunkRecord(
            id=f"{ingestion_id}_chunk_1",
            ingestion_id=ingestion_id,
            chunk_index=1,
            service_name="auth-service",
            severities_json=json.dumps(["ERROR"]),
            timestamp_start=datetime.now(timezone.utc),
            timestamp_end=datetime.now(timezone.utc),
            source_line_start=6,
            source_line_end=12,
            content=(
                "2026-11-01 10:05:00 ERROR [auth-service] HTTP 500 DB-1045 Access denied for user 'admin'@'localhost'\n"
                "Traceback:\n  File 'auth.py', line 54, in authenticate\n    raise ConnectionTimeoutError('timeout')"
            ),
        )
        chunk3 = LogChunkRecord(
            id=f"{ingestion_id}_chunk_2",
            ingestion_id=ingestion_id,
            chunk_index=2,
            service_name="payment-service",
            severities_json=json.dumps(["ERROR"]),
            timestamp_start=datetime.now(timezone.utc),
            timestamp_end=datetime.now(timezone.utc),
            source_line_start=13,
            source_line_end=20,
            content="2026-11-01 10:10:00 ERROR [payment-service] Gateway timeout contacting Stripe",
        )
        db.add_all([chunk1, chunk2, chunk3])
        db.commit()

    service = BM25SearchService()
    service.invalidate_cache()

    # Query exact error code DB-1045
    results = service.search(query="DB-1045", ingestion_id=ingestion_id)
    assert len(results) >= 1
    assert results[0]["chunk_id"] == f"{ingestion_id}_chunk_1"
    assert results[0]["bm25_score"] > 0
    assert results[0]["original_filename"] == "auth-service.log"
    assert results[0]["source_line_start"] == 6

    # Query HTTP 500
    http_results = service.search(query="HTTP 500", ingestion_id=ingestion_id)
    assert len(http_results) >= 1
    assert http_results[0]["chunk_id"] == f"{ingestion_id}_chunk_1"


def test_bm25_metadata_filtering():
    """Verify service and severity filters accurately filter candidates before ranking."""
    ingestion_id = "ingest_test_bm25_1"
    service = BM25SearchService()

    # Filter by service_name="payment-service"
    results_payment = service.search(query="timeout", service_name="payment-service", ingestion_id=ingestion_id)
    assert len(results_payment) == 1
    assert results_payment[0]["service_name"] == "payment-service"

    # Filter by non-existent severity for chunk_2 (which has ERROR)
    results_info = service.search(query="Gateway timeout", severity="INFO", ingestion_id=ingestion_id)
    assert len(results_info) == 0

    # Filter with matching severity
    results_err = service.search(query="Gateway timeout", severity="ERROR", ingestion_id=ingestion_id)
    assert len(results_err) >= 1
    assert results_err[0]["chunk_id"] == f"{ingestion_id}_chunk_2"

