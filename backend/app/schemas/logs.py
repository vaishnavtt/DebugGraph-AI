"""
Pydantic schemas for log ingestion, parsing, normalization, and event grouping.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


def current_utc_time() -> datetime:
    """Helper to return current UTC datetime."""
    return datetime.now(timezone.utc)


class LogEntry(BaseModel):
    """Structured representation of an individual log record."""

    entry_id: str = Field(..., description="Unique entry identifier")
    timestamp_raw: Optional[str] = Field(default=None, description="Original unparsed timestamp string")
    timestamp: Optional[datetime] = Field(default=None, description="Normalized UTC timestamp if parsed")
    severity: str = Field(
        default="UNKNOWN",
        description="Normalized severity level: DEBUG, INFO, WARNING, ERROR, CRITICAL, UNKNOWN",
    )
    service: Optional[str] = Field(default=None, description="Originating service or application name")
    message: str = Field(..., description="Extracted log message or text body")
    exception_type: Optional[str] = Field(default=None, description="Extracted exception class name")
    exception_message: Optional[str] = Field(default=None, description="Extracted exception detail message")
    stack_trace: Optional[str] = Field(default=None, description="Full multiline stack trace if present")
    start_line: int = Field(..., description="1-indexed starting line number in source file")
    end_line: int = Field(..., description="1-indexed ending line number in source file")
    raw_content: str = Field(..., description="Original raw text content")
    parsed: bool = Field(default=True, description="Whether record was parsed cleanly or preserved unparsed")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary structured metadata (e.g., request_id, thread, trace_id, HTTP status)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entry_id": "log_001",
                "timestamp_raw": "2026-11-01 10:15:01",
                "timestamp": "2026-11-01T10:15:01Z",
                "severity": "ERROR",
                "service": "payment-service",
                "message": "Database connection timeout during checkout",
                "exception_type": "ConnectionTimeoutError",
                "exception_message": "Failed to connect to postgres:5432 after 3000ms",
                "stack_trace": "Traceback (most recent call last):\n  File ...",
                "start_line": 42,
                "end_line": 48,
                "raw_content": "2026-11-01 10:15:01 ERROR [payment-service] Database connection timeout...",
                "parsed": True,
                "attributes": {"correlation_id": "req-9876"},
            }
        }
    )


class LogEventGroup(BaseModel):
    """Correlated cluster of related log events."""

    group_id: str = Field(..., description="Unique event group identifier")
    group_type: str = Field(
        ...,
        description="Correlation rationale: shared_correlation_id, common_exception, or temporal_proximity",
    )
    service: Optional[str] = Field(default=None, description="Common service involved, if consistent")
    description: str = Field(..., description="Human-readable explanation of the correlation")
    entry_ids: List[str] = Field(default_factory=list, description="IDs of enclosed log entries")
    entry_count: int = Field(..., description="Total count of associated log entries")
    start_timestamp: Optional[datetime] = Field(default=None, description="Earliest timestamp in group")
    end_timestamp: Optional[datetime] = Field(default=None, description="Latest timestamp in group")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "group_id": "grp_001",
                "group_type": "shared_correlation_id",
                "service": "payment-service",
                "description": "Correlated events sharing correlation_id: req-9876",
                "entry_ids": ["log_001", "log_002"],
                "entry_count": 2,
                "start_timestamp": "2026-11-01T10:15:01Z",
                "end_timestamp": "2026-11-01T10:15:03Z",
            }
        }
    )


class LogIngestionSummary(BaseModel):
    """Aggregate statistics for an ingested log file."""

    total_entries: int = Field(..., description="Total log entries parsed or recorded")
    parsed_entries: int = Field(..., description="Entries conforming to recognized schemas")
    unparsed_entries: int = Field(..., description="Entries preserved without recognized schema")
    debug_count: int = Field(default=0, description="Count of DEBUG severity entries")
    info_count: int = Field(default=0, description="Count of INFO severity entries")
    warning_count: int = Field(default=0, description="Count of WARNING severity entries")
    error_count: int = Field(default=0, description="Count of ERROR severity entries")
    critical_count: int = Field(default=0, description="Count of CRITICAL severity entries")
    unknown_count: int = Field(default=0, description="Count of UNKNOWN severity entries")


class LogUploadResponse(BaseModel):
    """Response payload returned upon successfully uploading and parsing a log file."""

    ingestion_id: str = Field(..., description="Unique identifier for this ingestion job")
    original_filename: str = Field(..., description="Sanitized original filename")
    file_size_bytes: int = Field(..., description="Size of uploaded content in bytes")
    format_detected: str = Field(..., description="Detected format: json, jsonl, or standard_text")
    total_entries: int = Field(..., description="Total entries identified")
    parsed_entries: int = Field(..., description="Number of successfully parsed structured records")
    unparsed_entries: int = Field(..., description="Number of unparsed fallback records")
    error_count: int = Field(..., description="Total error severity entries")
    warning_count: int = Field(..., description="Total warning severity entries")
    critical_count: int = Field(..., description="Total critical severity entries")
    summary: LogIngestionSummary = Field(..., description="Complete breakdown of ingestion statistics")
    event_groups: List[LogEventGroup] = Field(
        default_factory=list,
        description="Correlated clusters of events based on correlation IDs, exceptions, and proximity",
    )
    parsing_warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings or anomalies encountered during ingestion",
    )
    timestamp: datetime = Field(default_factory=current_utc_time, description="UTC completion timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ingestion_id": "ingest_a1b2c3d4",
                "original_filename": "payment-service.log",
                "file_size_bytes": 10240,
                "format_detected": "standard_text",
                "total_entries": 120,
                "parsed_entries": 118,
                "unparsed_entries": 2,
                "error_count": 5,
                "warning_count": 12,
                "critical_count": 1,
                "summary": {
                    "total_entries": 120,
                    "parsed_entries": 118,
                    "unparsed_entries": 2,
                    "debug_count": 0,
                    "info_count": 100,
                    "warning_count": 12,
                    "error_count": 5,
                    "critical_count": 1,
                    "unknown_count": 2,
                },
                "event_groups": [],
                "parsing_warnings": ["Line 45 could not be parsed as standard timestamp."],
                "timestamp": "2026-11-01T10:16:00Z",
            }
        }
    )

