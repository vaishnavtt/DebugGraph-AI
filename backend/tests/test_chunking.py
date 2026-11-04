"""
Unit tests for intelligent log chunking engine.
Validates entry integrity, stack trace preservation, metadata extraction, and overlap.
"""
from datetime import datetime, timezone
import pytest

from app.retrieval.chunking import LogChunker
from app.schemas.logs import LogEntry


def test_chunk_creation_preserves_entries() -> None:
    """Ensure chunking groups entries without slicing individual records."""
    entries = [
        LogEntry(
            entry_id=f"log_{i}",
            timestamp=datetime(2026, 11, 1, 10, i, 0, tzinfo=timezone.utc),
            timestamp_raw=f"2026-11-01 10:{i:02d}:00",
            severity="INFO",
            service="order-service",
            message=f"Processing order batch step {i}",
            start_line=i * 2 + 1,
            end_line=i * 2 + 2,
            raw_content=f"2026-11-01 10:{i:02d}:00 INFO Step {i}",
        )
        for i in range(15)
    ]

    chunker = LogChunker(max_entries_per_chunk=5, overlap_entries=1)
    chunks = chunker.create_chunks(entries, ingestion_id="ingest_test_1", original_filename="orders.log")

    assert len(chunks) >= 3
    # Verify each chunk has a valid chunk_id
    assert chunks[0].chunk_id == "ingest_test_1_chunk_0"
    assert chunks[1].chunk_id == "ingest_test_1_chunk_1"

    # Verify line numbers are correctly bounded
    assert chunks[0].source_line_start == 1
    assert chunks[0].source_line_end >= 10
    assert "order-service" in chunks[0].services


def test_multiline_exception_preservation_in_chunk() -> None:
    """Ensure stack traces are not split or truncated during chunking."""
    stack_trace = (
        "Traceback (most recent call last):\n"
        "  File '/app/main.py', line 45, in run\n"
        "    db.connect()\n"
        "ConnectionTimeoutError: Database connect timed out"
    )

    error_entry = LogEntry(
        entry_id="log_err",
        timestamp=datetime(2026, 11, 1, 10, 15, 0, tzinfo=timezone.utc),
        timestamp_raw="2026-11-01 10:15:00",
        severity="ERROR",
        service="payment-service",
        message="Checkout failed due to DB timeout",
        exception_type="ConnectionTimeoutError",
        exception_message="Database connect timed out",
        stack_trace=stack_trace,
        start_line=10,
        end_line=14,
        raw_content=f"2026-11-01 10:15:00 ERROR Checkout failed\n{stack_trace}",
    )

    chunker = LogChunker(max_entries_per_chunk=3)
    chunks = chunker.create_chunks([error_entry], ingestion_id="ingest_err", original_filename="error.log")

    assert len(chunks) == 1
    chunk = chunks[0]
    assert "ConnectionTimeoutError" in chunk.exception_signatures
    assert "Traceback (most recent call last):" in chunk.content
    assert chunk.source_line_start == 10
    assert chunk.source_line_end == 14
    assert chunk.service_name == "payment-service"


def test_metadata_preservation_in_chunk() -> None:
    """Ensure all required structured payload metadata fields are present."""
    entry = LogEntry(
        entry_id="log_meta",
        timestamp=datetime(2026, 11, 1, 10, 30, 0, tzinfo=timezone.utc),
        timestamp_raw="2026-11-01 10:30:00",
        severity="CRITICAL",
        service="auth-service",
        message="Redis cluster partition",
        start_line=1,
        end_line=2,
        raw_content="2026-11-01 10:30:00 CRITICAL Redis cluster partition",
        attributes={"request_id": "req-99901", "trace_id": "trace-abc-123"},
    )

    chunker = LogChunker()
    chunks = chunker.create_chunks([entry], ingestion_id="ingest_meta", original_filename="auth.log")

    assert len(chunks) == 1
    meta = chunks[0].metadata
    assert meta["ingestion_id"] == "ingest_meta"
    assert meta["original_filename"] == "auth.log"
    assert meta["service_name"] == "auth-service"
    assert "CRITICAL" in meta["severities"]
    assert "req-99901" in meta["request_ids"]
    assert meta["source_line_start"] == 1
    assert meta["source_line_end"] == 2


def test_empty_entries_handling() -> None:
    """Ensure empty input returns empty list without error."""
    chunker = LogChunker()
    chunks = chunker.create_chunks([], ingestion_id="ingest_empty", original_filename="empty.log")
    assert chunks == []

