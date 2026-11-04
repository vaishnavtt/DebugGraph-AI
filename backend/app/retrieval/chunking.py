"""
Intelligent Log Chunking Engine for DebugGraph AI.
Groups related consecutive log entries into semantically coherent chunks,
preserving complete multiline stack traces and structured metadata.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.logs import LogEntry


class LogChunk(BaseModel):
    """Searchable vector chunk containing grouped log entries and rich metadata."""

    chunk_id: str = Field(..., description="Stable unique chunk identifier")
    ingestion_id: str = Field(..., description="Parent ingestion run identifier")
    chunk_index: int = Field(..., description="0-indexed position within the document")
    content: str = Field(..., description="Searchable textual representation of grouped entries")
    service_name: Optional[str] = Field(default=None, description="Primary service name involved")
    services: List[str] = Field(default_factory=list, description="All service names in chunk")
    severities: List[str] = Field(default_factory=list, description="Unique severity levels in chunk")
    timestamp_start: Optional[datetime] = Field(default=None, description="Earliest timestamp in chunk")
    timestamp_end: Optional[datetime] = Field(default=None, description="Latest timestamp in chunk")
    source_line_start: int = Field(..., description="Earliest source line number")
    source_line_end: int = Field(..., description="Latest source line number")
    source_entry_ids: List[str] = Field(default_factory=list, description="Enclosed log entry IDs")
    exception_signatures: List[str] = Field(default_factory=list, description="Identified exception types")
    request_ids: List[str] = Field(default_factory=list, description="Associated correlation and request IDs")
    original_filename: str = Field(..., description="Source log file name")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Structured Qdrant payload")


class LogChunker:
    """Chunking orchestrator grouping entries without slicing individual records."""

    def __init__(
        self,
        max_entries_per_chunk: int = 10,
        max_chars_per_chunk: int = 2500,
        overlap_entries: int = 2,
    ) -> None:
        self.max_entries_per_chunk = max(1, max_entries_per_chunk)
        self.max_chars_per_chunk = max_chars_per_chunk
        self.overlap_entries = max(0, min(overlap_entries, self.max_entries_per_chunk - 1))

    def create_chunks(
        self,
        entries: List[LogEntry],
        ingestion_id: str,
        original_filename: str,
    ) -> List[LogChunk]:
        """
        Split a sequence of log entries into overlapping chunks.
        Guarantees that individual log entries (and their multiline stack traces)
        are never split across chunk boundaries.
        """
        if not entries:
            return []

        chunks: List[LogChunk] = []
        total_entries = len(entries)
        i = 0
        chunk_index = 0

        while i < total_entries:
            chunk_entries: List[LogEntry] = []
            current_chars = 0
            j = i

            while j < total_entries:
                entry = entries[j]
                entry_len = len(entry.raw_content)

                # Include at least one entry even if it exceeds max_chars_per_chunk
                if chunk_entries and (
                    len(chunk_entries) >= self.max_entries_per_chunk
                    or (current_chars + entry_len > self.max_chars_per_chunk)
                ):
                    break

                chunk_entries.append(entry)
                current_chars += entry_len
                j += 1

            # Format searchable text content for embedding
            text_lines: List[str] = []
            for e in chunk_entries:
                ts_str = e.timestamp.isoformat() if e.timestamp else (e.timestamp_raw or "NO_TIME")
                svc_str = f"[{e.service}] " if e.service else ""
                header = f"{ts_str} {e.severity} {svc_str}{e.message}"
                if e.stack_trace:
                    header += f"\n{e.stack_trace}"
                text_lines.append(header)

            content = "\n---\n".join(text_lines)

            # Aggregate metadata
            services = sorted(list({e.service for e in chunk_entries if e.service}))
            primary_service = services[0] if len(services) == 1 else (services[0] if services else None)
            severities = sorted(list({e.severity for e in chunk_entries if e.severity}))

            timestamps = [e.timestamp for e in chunk_entries if e.timestamp]
            ts_start = min(timestamps) if timestamps else None
            ts_end = max(timestamps) if timestamps else None

            start_line = min(e.start_line for e in chunk_entries)
            end_line = max(e.end_line for e in chunk_entries)
            entry_ids = [e.entry_id for e in chunk_entries]

            exceptions = sorted(list({e.exception_type for e in chunk_entries if e.exception_type}))
            request_ids = sorted(
                list(
                    {
                        str(e.attributes[k])
                        for e in chunk_entries
                        for k in ("request_id", "correlation_id", "trace_id")
                        if k in e.attributes and e.attributes[k]
                    }
                )
            )

            chunk_id = f"{ingestion_id}_chunk_{chunk_index}"

            payload_metadata: Dict[str, Any] = {
                "chunk_id": chunk_id,
                "ingestion_id": ingestion_id,
                "chunk_index": chunk_index,
                "original_filename": original_filename,
                "service_name": primary_service,
                "services": services,
                "severities": severities,
                "severity": severities[-1] if severities else "UNKNOWN",
                "timestamp_start": ts_start.isoformat() if ts_start else None,
                "timestamp_end": ts_end.isoformat() if ts_end else None,
                "source_line_start": start_line,
                "source_line_end": end_line,
                "source_entry_ids": entry_ids,
                "exception_signatures": exceptions,
                "request_ids": request_ids,
                "entry_count": len(chunk_entries),
            }

            chunk = LogChunk(
                chunk_id=chunk_id,
                ingestion_id=ingestion_id,
                chunk_index=chunk_index,
                content=content,
                service_name=primary_service,
                services=services,
                severities=severities,
                timestamp_start=ts_start,
                timestamp_end=ts_end,
                source_line_start=start_line,
                source_line_end=end_line,
                source_entry_ids=entry_ids,
                exception_signatures=exceptions,
                request_ids=request_ids,
                original_filename=original_filename,
                metadata=payload_metadata,
            )
            chunks.append(chunk)
            chunk_index += 1

            # Advance with overlap
            advance = len(chunk_entries) - self.overlap_entries
            if advance <= 0 or j >= total_entries:
                break
            i += advance

        return chunks

