"""
Tests for log parsing, normalization, and event grouping engines.
"""
from datetime import datetime, timezone
import pytest

from app.ingestion.event_grouper import EventGrouper
from app.ingestion.log_parser import LogParser, extract_exception_details
from app.ingestion.normalizer import normalize_severity, normalize_timestamp
from app.schemas.logs import LogEntry


def test_standard_text_log_parsing() -> None:
    """Validate standard single-line log parsing with timestamp, severity, service, and message."""
    raw_logs = (
        "2026-11-01 10:15:01 INFO [payment-service] Payment gateway initialized\n"
        "2026-11-01 10:15:02 WARNING [payment-service] High latency detected: 850ms\n"
    )
    entries, warnings = LogParser.parse_text_logs(raw_logs)

    assert len(entries) == 2
    assert entries[0].severity == "INFO"
    assert entries[0].service == "payment-service"
    assert entries[0].message == "Payment gateway initialized"
    assert entries[0].timestamp == datetime(2026, 11, 1, 10, 15, 1, tzinfo=timezone.utc)
    assert entries[0].start_line == 1
    assert entries[0].end_line == 1

    assert entries[1].severity == "WARNING"
    assert entries[1].service == "payment-service"
    assert entries[1].message == "High latency detected: 850ms"
    assert entries[1].start_line == 2
    assert entries[1].end_line == 2


def test_multiline_python_exception_handling() -> None:
    """Validate that Python stack traces are bound to their originating entry and properly parsed."""
    raw_logs = (
        "2026-11-01 10:15:15 ERROR [order-service] Failed to checkout cart\n"
        "Traceback (most recent call last):\n"
        "  File \"/app/checkout.py\", line 45, in checkout\n"
        "    payment_client.charge(cart_id)\n"
        "  File \"/app/payment.py\", line 12, in charge\n"
        "    raise ConnectionTimeoutError(\"Payment service timeout after 5000ms\")\n"
        "ConnectionTimeoutError: Payment service timeout after 5000ms\n"
        "2026-11-01 10:15:16 INFO [order-service] Retrying checkout for cart\n"
    )
    entries, warnings = LogParser.parse_text_logs(raw_logs)

    assert len(entries) == 2
    error_entry = entries[0]
    assert error_entry.severity == "ERROR"
    assert error_entry.service == "order-service"
    assert "Failed to checkout cart" in error_entry.message
    assert error_entry.start_line == 1
    assert error_entry.end_line == 7
    assert error_entry.stack_trace is not None
    assert "Traceback (most recent call last):" in error_entry.stack_trace
    assert error_entry.exception_type == "ConnectionTimeoutError"
    assert error_entry.exception_message == "Payment service timeout after 5000ms"

    next_entry = entries[1]
    assert next_entry.severity == "INFO"
    assert next_entry.start_line == 8
    assert next_entry.end_line == 8


def test_json_parsing() -> None:
    """Validate parsing of structured JSON array logs."""
    raw_json = """[
        {
            "timestamp": "2026-11-01T10:15:01Z",
            "level": "INFO",
            "service": "auth-service",
            "message": "User login successful",
            "user_id": "usr_123",
            "request_id": "req-99"
        },
        {
            "timestamp": "2026-11-01T10:15:05Z",
            "level": "ERROR",
            "service": "auth-service",
            "message": "Token verification failed",
            "exception": {
                "type": "InvalidSignatureError",
                "message": "Signature has expired",
                "stack_trace": "Traceback ... InvalidSignatureError: Signature has expired"
            }
        }
    ]"""
    entries, warnings = LogParser.parse_json_content(raw_json)

    assert len(entries) == 2
    assert entries[0].service == "auth-service"
    assert entries[0].severity == "INFO"
    assert entries[0].attributes.get("request_id") == "req-99"
    assert entries[0].attributes.get("user_id") == "usr_123"

    assert entries[1].severity == "ERROR"
    assert entries[1].exception_type == "InvalidSignatureError"
    assert entries[1].exception_message == "Signature has expired"


def test_jsonl_parsing() -> None:
    """Validate parsing of JSON Lines (JSONL) records."""
    raw_jsonl = (
        '{"timestamp": "2026-11-01T10:15:01Z", "level": "INFO", "service": "api-gateway", "message": "GET /api/v1/orders 200"}\n'
        '{"timestamp": "2026-11-01T10:15:02Z", "level": "WARN", "service": "api-gateway", "message": "High memory usage: 88%"}\n'
    )
    entries, warnings = LogParser.parse_jsonl_content(raw_jsonl)

    assert len(entries) == 2
    assert entries[0].service == "api-gateway"
    assert entries[0].severity == "INFO"
    assert entries[1].severity == "WARNING"


def test_invalid_timestamps() -> None:
    """Ensure invalid timestamps do not crash parsing and raw strings are preserved."""
    dt, raw = normalize_timestamp("not-a-timestamp-1234")
    assert dt is None
    assert raw == "not-a-timestamp-1234"

    raw_log = "2026-99-99 99:99:99 INFO [payment-service] Message with invalid date\n"
    entries, warnings = LogParser.parse_text_logs(raw_log)
    assert len(entries) == 1
    assert entries[0].timestamp is None
    assert entries[0].timestamp_raw == "2026-99-99 99:99:99"


def test_unknown_severity() -> None:
    """Ensure arbitrary or unmapped severity values map to UNKNOWN without crashing."""
    assert normalize_severity("RANDOM_LEVEL") == "UNKNOWN"
    assert normalize_severity("") == "UNKNOWN"
    assert normalize_severity(None) == "UNKNOWN"
    assert normalize_severity("WARN") == "WARNING"
    assert normalize_severity("FATAL") == "CRITICAL"
    assert normalize_severity("ERR") == "ERROR"


def test_unrecognized_log_lines_preserved() -> None:
    """Ensure non-standard log lines are preserved as unparsed records with no silent data loss."""
    raw_logs = "Something went completely wrong without any timestamp or format header!\n"
    entries, warnings = LogParser.parse_text_logs(raw_logs)

    assert len(entries) == 1
    assert entries[0].parsed is False
    assert entries[0].severity == "UNKNOWN"
    assert "Something went completely wrong" in entries[0].message
    assert len(warnings) >= 1


def test_event_grouping_shared_correlation_id() -> None:
    """Verify grouping of events sharing a request/correlation ID."""
    e1 = LogEntry(
        entry_id="e1",
        start_line=1,
        end_line=1,
        raw_content="log 1",
        message="Order initiated",
        severity="INFO",
        service="order-service",
        timestamp=datetime(2026, 11, 1, 10, 0, 0, tzinfo=timezone.utc),
        attributes={"request_id": "req-xyz-100"},
    )
    e2 = LogEntry(
        entry_id="e2",
        start_line=2,
        end_line=2,
        raw_content="log 2",
        message="Payment processed",
        severity="INFO",
        service="order-service",
        timestamp=datetime(2026, 11, 1, 10, 0, 2, tzinfo=timezone.utc),
        attributes={"request_id": "req-xyz-100"},
    )

    groups = EventGrouper.group_events([e1, e2])
    corr_groups = [g for g in groups if g.group_type == "shared_correlation_id"]

    assert len(corr_groups) == 1
    assert corr_groups[0].entry_count == 2
    assert "req-xyz-100" in corr_groups[0].description
    assert corr_groups[0].entry_ids == ["e1", "e2"]


def test_event_grouping_common_exception() -> None:
    """Verify grouping of recurring exceptions."""
    e1 = LogEntry(
        entry_id="e1",
        start_line=1,
        end_line=5,
        raw_content="err 1",
        message="DB connect failed",
        severity="ERROR",
        service="payment-service",
        exception_type="DatabaseTimeoutError",
        timestamp=datetime(2026, 11, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    e2 = LogEntry(
        entry_id="e2",
        start_line=6,
        end_line=10,
        raw_content="err 2",
        message="DB connect retry failed",
        severity="ERROR",
        service="payment-service",
        exception_type="DatabaseTimeoutError",
        timestamp=datetime(2026, 11, 1, 10, 0, 5, tzinfo=timezone.utc),
    )

    groups = EventGrouper.group_events([e1, e2])
    exc_groups = [g for g in groups if g.group_type == "common_exception"]

    assert len(exc_groups) == 1
    assert "DatabaseTimeoutError" in exc_groups[0].description
    assert exc_groups[0].entry_count == 2


def test_event_grouping_temporal_proximity() -> None:
    """Verify temporal proximity clustering does not assert causal claims."""
    e1 = LogEntry(
        entry_id="e1",
        start_line=1,
        end_line=1,
        raw_content="err 1",
        message="Downstream error A",
        severity="ERROR",
        service="svc-a",
        timestamp=datetime(2026, 11, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    e2 = LogEntry(
        entry_id="e2",
        start_line=2,
        end_line=2,
        raw_content="err 2",
        message="Downstream error B",
        severity="CRITICAL",
        service="svc-b",
        timestamp=datetime(2026, 11, 1, 10, 0, 15, tzinfo=timezone.utc),
    )

    groups = EventGrouper.group_events([e1, e2], temporal_window_seconds=30)
    temp_groups = [g for g in groups if g.group_type == "temporal_proximity"]

    assert len(temp_groups) == 1
    assert "temporal proximity only; non-causal" in temp_groups[0].description

