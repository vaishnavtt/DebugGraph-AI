"""
SQLAlchemy ORM models for DebugGraph AI.
Provides persistent storage for ingestion runs, parsed log entries, and vector chunk metadata.
"""
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class IngestionRecord(Base):
    """Stores metadata and aggregate metrics for an uploaded log file ingestion."""

    __tablename__ = "ingestion_records"

    id = Column(String(64), primary_key=True, index=True)  # e.g., "ingest_a1b2c3d4"
    filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    format_detected = Column(String(32), nullable=False)
    total_entries = Column(Integer, default=0, nullable=False)
    parsed_entries = Column(Integer, default=0, nullable=False)
    unparsed_entries = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    warning_count = Column(Integer, default=0, nullable=False)
    critical_count = Column(Integer, default=0, nullable=False)
    indexing_status = Column(String(32), default="pending", nullable=False, index=True)  # pending, indexed, failed
    indexed_chunks_count = Column(Integer, default=0, nullable=False)
    summary_json = Column(Text, nullable=True)
    event_groups_json = Column(Text, nullable=True)
    parsing_warnings_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    entries = relationship(
        "ParsedLogEntryModel",
        back_populates="ingestion",
        cascade="all, delete-orphan",
        order_by="ParsedLogEntryModel.id",
    )
    chunks = relationship(
        "LogChunkRecord",
        back_populates="ingestion",
        cascade="all, delete-orphan",
        order_by="LogChunkRecord.chunk_index",
    )


class ParsedLogEntryModel(Base):
    """Stores individual structured and normalized log entries."""

    __tablename__ = "parsed_log_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(64), nullable=False)  # e.g., "log_1"
    ingestion_id = Column(
        String(64),
        ForeignKey("ingestion_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp = Column(DateTime(timezone=True), nullable=True, index=True)
    timestamp_raw = Column(String(128), nullable=True)
    severity = Column(String(32), default="UNKNOWN", nullable=False, index=True)
    service = Column(String(128), nullable=True, index=True)
    message = Column(Text, nullable=False)
    exception_type = Column(String(128), nullable=True, index=True)
    exception_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    raw_content = Column(Text, nullable=False)
    parsed = Column(Boolean, default=True, nullable=False)
    attributes_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    ingestion = relationship("IngestionRecord", back_populates="entries")


class LogChunkRecord(Base):
    """Metadata for searchable vector chunks associated with an ingestion."""

    __tablename__ = "log_chunks"

    id = Column(String(128), primary_key=True, index=True)  # e.g. "ingest_xxx_chunk_0"
    ingestion_id = Column(
        String(64),
        ForeignKey("ingestion_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False)
    service_name = Column(String(128), nullable=True, index=True)
    severities_json = Column(Text, nullable=True)
    timestamp_start = Column(DateTime(timezone=True), nullable=True)
    timestamp_end = Column(DateTime(timezone=True), nullable=True)
    source_line_start = Column(Integer, nullable=False)
    source_line_end = Column(Integer, nullable=False)
    source_entry_ids_json = Column(Text, nullable=True)
    exception_signatures_json = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    ingestion = relationship("IngestionRecord", back_populates="chunks")

