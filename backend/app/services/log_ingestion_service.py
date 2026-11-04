"""
Log Ingestion Service for DebugGraph AI.
Coordinates file validation, format detection, parsing, normalization,
event correlation grouping, and statistical summarization.
"""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import List, Optional, Set, Tuple
import uuid

from fastapi import status

from app.core.config import settings
from app.core.errors import AppException
from app.core.logging import get_logger
from app.database.models import IngestionRecord, ParsedLogEntryModel
from app.database.session import get_db_context
from app.ingestion.event_grouper import EventGrouper
from app.ingestion.log_parser import LogParser
from app.schemas.logs import (
    LogEntry,
    LogIngestionSummary,
    LogUploadResponse,
)

logger = get_logger(__name__)

ALLOWED_EXTENSIONS: Set[str] = {".log", ".txt", ".json", ".jsonl"}


class LogIngestionService:
    """Service handling file upload validation, parsing orchestration, and analytics."""

    @staticmethod
    def sanitize_filename(raw_filename: Optional[str]) -> str:
        """Sanitize filename to prevent directory traversal and null byte injections."""
        if not raw_filename or not raw_filename.strip():
            return "unnamed_log.log"

        # Extract only the base name (strip directory parts)
        safe_name = Path(raw_filename).name
        # Remove null bytes and control characters
        safe_name = re.sub(r"[\x00-\x1f\x7f]", "", safe_name).strip()

        if not safe_name or safe_name in (".", ".."):
            return "unnamed_log.log"

        return safe_name

    @classmethod
    def validate_file_metadata(cls, filename: str, content_size: int) -> str:
        """Validate file extension and file size constraints."""
        safe_filename = cls.sanitize_filename(filename)
        ext = Path(safe_filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="UNSUPPORTED_FILE_TYPE",
                message=(
                    f"File extension '{ext}' is unsupported. "
                    f"Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
                ),
            )

        if content_size == 0:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="EMPTY_FILE",
                message="Uploaded file is empty.",
            )

        if content_size > settings.MAX_LOG_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_LOG_UPLOAD_SIZE_BYTES / (1024 * 1024)
            raise AppException(
                status_code=413,
                code="FILE_TOO_LARGE",
                message=f"File size exceeds maximum permitted limit of {max_mb:.1f} MB.",
            )

        return safe_filename

    @classmethod
    def detect_format(cls, filename: str, content_str: str) -> str:
        """Determine whether content should be processed as json, jsonl, or standard_text."""
        ext = Path(filename).suffix.lower()
        if ext == ".jsonl":
            return "jsonl"
        if ext == ".json":
            return "json"

        # Content sniffing fallback for .log or .txt
        stripped = content_str.lstrip()
        if stripped.startswith("[") and stripped.rstrip().endswith("]"):
            return "json"
        if stripped.startswith("{") and "\n{" in stripped:
            return "jsonl"

        return "standard_text"

    @classmethod
    def process_log_upload(
        cls,
        raw_bytes: bytes,
        original_filename: Optional[str] = None,
        default_service: Optional[str] = None,
    ) -> LogUploadResponse:
        """
        Main pipeline coordinating validation, parsing, normalization,
        event grouping, and statistical breakdown.
        """
        content_size = len(raw_bytes)
        safe_filename = cls.validate_file_metadata(original_filename or "upload.log", content_size)

        # Decode content safely without crashing on invalid byte sequences
        try:
            content_str = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content_str = raw_bytes.decode("latin-1")
            except Exception as exc:
                raise AppException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    code="MALFORMED_ENCODING",
                    message="Uploaded file cannot be decoded as UTF-8 or Latin-1 text.",
                ) from exc

        if not content_str.strip():
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="EMPTY_FILE",
                message="Uploaded file contains only whitespace.",
            )

        ingestion_id = f"ingest_{uuid.uuid4().hex[:12]}"
        format_detected = cls.detect_format(safe_filename, content_str)

        entries: List[LogEntry] = []
        parsing_warnings: List[str] = []

        # Route to appropriate parsing strategy
        if format_detected == "json":
            entries, parsing_warnings = LogParser.parse_json_content(content_str, default_service=default_service)
            if not entries and parsing_warnings:
                # If json decoding completely failed on a .json file, raise clear error
                raise AppException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    code="MALFORMED_JSON",
                    message=f"Failed to parse JSON file: {parsing_warnings[0]}",
                    details=parsing_warnings,
                )
        elif format_detected == "jsonl":
            entries, parsing_warnings = LogParser.parse_jsonl_content(content_str, default_service=default_service)
        else:
            entries, parsing_warnings = LogParser.parse_text_logs(content_str, default_service=default_service)

        # Ingestion Statistics
        total_entries = len(entries)
        parsed_entries = sum(1 for e in entries if e.parsed)
        unparsed_entries = total_entries - parsed_entries

        severity_counts = Counter(e.severity for e in entries)
        error_count = severity_counts.get("ERROR", 0)
        warning_count = severity_counts.get("WARNING", 0)
        critical_count = severity_counts.get("CRITICAL", 0)

        summary = LogIngestionSummary(
            total_entries=total_entries,
            parsed_entries=parsed_entries,
            unparsed_entries=unparsed_entries,
            debug_count=severity_counts.get("DEBUG", 0),
            info_count=severity_counts.get("INFO", 0),
            warning_count=warning_count,
            error_count=error_count,
            critical_count=critical_count,
            unknown_count=severity_counts.get("UNKNOWN", 0),
        )

        # Correlate events into clusters
        event_groups = EventGrouper.group_events(entries)

        # Persist ingestion run and parsed entries to database
        try:
            with get_db_context() as db:
                record = IngestionRecord(
                    id=ingestion_id,
                    filename=safe_filename,
                    file_size_bytes=content_size,
                    format_detected=format_detected,
                    total_entries=total_entries,
                    parsed_entries=parsed_entries,
                    unparsed_entries=unparsed_entries,
                    error_count=error_count,
                    warning_count=warning_count,
                    critical_count=critical_count,
                    indexing_status="pending",
                    indexed_chunks_count=0,
                    summary_json=summary.model_dump_json(),
                    event_groups_json=json.dumps([g.model_dump(mode="json") for g in event_groups]),
                    parsing_warnings_json=json.dumps(parsing_warnings),
                )
                db.add(record)

                entry_models = [
                    ParsedLogEntryModel(
                        entry_id=e.entry_id,
                        ingestion_id=ingestion_id,
                        timestamp=e.timestamp,
                        timestamp_raw=e.timestamp_raw,
                        severity=e.severity,
                        service=e.service,
                        message=e.message,
                        exception_type=e.exception_type,
                        exception_message=e.exception_message,
                        stack_trace=e.stack_trace,
                        start_line=e.start_line,
                        end_line=e.end_line,
                        raw_content=e.raw_content,
                        parsed=e.parsed,
                        attributes_json=json.dumps(e.attributes) if e.attributes else None,
                    )
                    for e in entries
                ]
                db.add_all(entry_models)
                db.commit()
                logger.info(
                    "Persisted ingestion %s with %d entries to database",
                    ingestion_id,
                    len(entry_models),
                )
        except Exception as exc:
            logger.error("Failed to persist ingestion to database: %s", exc, exc_info=True)

        logger.info(
            "Ingestion completed: ID=%s, File=%s, Total=%d, Parsed=%d, Errors=%d, Groups=%d",
            ingestion_id,
            safe_filename,
            total_entries,
            parsed_entries,
            error_count,
            len(event_groups),
        )

        return LogUploadResponse(
            ingestion_id=ingestion_id,
            original_filename=safe_filename,
            file_size_bytes=content_size,
            format_detected=format_detected,
            total_entries=total_entries,
            parsed_entries=parsed_entries,
            unparsed_entries=unparsed_entries,
            error_count=error_count,
            warning_count=warning_count,
            critical_count=critical_count,
            summary=summary,
            event_groups=event_groups,
            parsing_warnings=parsing_warnings,
            timestamp=datetime.now(timezone.utc),
        )
