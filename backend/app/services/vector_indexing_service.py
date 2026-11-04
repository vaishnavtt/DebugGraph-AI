"""
Vector Indexing Service for DebugGraph AI.
Coordinates chunking of persisted log entries, embedding generation,
and idempotent indexing into the Qdrant vector database.
"""
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional

from fastapi import status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppException
from app.core.logging import get_logger
from app.database.models import IngestionRecord, LogChunkRecord, ParsedLogEntryModel
from app.database.session import get_db_context
from app.retrieval.chunking import LogChunk, LogChunker
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import QdrantVectorStore
from app.schemas.indexing import (
    IndexingResponse,
    IndexingStatusResponse,
    SearchResultHit,
    SemanticSearchRequest,
    SemanticSearchResponse,
)
from app.schemas.logs import LogEntry

logger = get_logger(__name__)


class VectorIndexingService:
    """Service orchestrating log chunking, embedding generation, and vector indexing."""

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[QdrantVectorStore] = None,
        chunker: Optional[LogChunker] = None,
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService.get_instance()
        self.vector_store = vector_store or QdrantVectorStore()
        self.chunker = chunker or LogChunker()

    def index_ingestion(self, ingestion_id: str) -> IndexingResponse:
        """
        Idempotently indexes an ingestion's parsed log entries into Qdrant.
        Retrieves entries from persistent database storage, chunks them,
        generates dense embeddings, and stores vectors with structured payloads.
        """
        logger.info("Initiating vector indexing for ingestion '%s'...", ingestion_id)

        with get_db_context() as db:
            record: Optional[IngestionRecord] = (
                db.query(IngestionRecord).filter(IngestionRecord.id == ingestion_id).first()
            )
            if not record:
                raise AppException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code="INGESTION_NOT_FOUND",
                    message=f"Ingestion '{ingestion_id}' does not exist in persistent database.",
                )

            # Retrieve persisted log entries
            entry_models: List[ParsedLogEntryModel] = (
                db.query(ParsedLogEntryModel)
                .filter(ParsedLogEntryModel.ingestion_id == ingestion_id)
                .order_by(ParsedLogEntryModel.id.asc())
                .all()
            )

            if not entry_models:
                raise AppException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    code="NO_LOG_ENTRIES",
                    message=f"Ingestion '{ingestion_id}' has no log entries available for indexing.",
                )

            # Convert ORM records into LogEntry domain models
            domain_entries: List[LogEntry] = []
            for m in entry_models:
                attributes: Dict[str, Any] = {}
                if m.attributes_json:
                    try:
                        attributes = json.loads(m.attributes_json)
                    except Exception:
                        attributes = {}

                domain_entries.append(
                    LogEntry(
                        entry_id=m.entry_id,
                        timestamp=m.timestamp,
                        timestamp_raw=m.timestamp_raw,
                        severity=m.severity,
                        service=m.service,
                        message=m.message,
                        exception_type=m.exception_type,
                        exception_message=m.exception_message,
                        stack_trace=m.stack_trace,
                        start_line=m.start_line,
                        end_line=m.end_line,
                        raw_content=m.raw_content,
                        parsed=m.parsed,
                        attributes=attributes,
                    )
                )

            filename = record.filename

        # 1. Chunk log entries
        chunks: List[LogChunk] = self.chunker.create_chunks(
            entries=domain_entries,
            ingestion_id=ingestion_id,
            original_filename=filename,
        )

        if not chunks:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="CHUNKING_FAILED",
                message="No chunks could be produced from log entries.",
            )

        # 2. Generate embeddings
        chunk_texts = [c.content for c in chunks]
        vectors = self.embedding_service.embed_documents(chunk_texts)

        # 3. Ensure vector collection exists
        self.vector_store.ensure_collection()

        # 4. Idempotently clean up any prior vectors for this ingestion ID
        self.vector_store.delete_by_ingestion_id(ingestion_id)

        # 5. Insert vectors into Qdrant
        self.vector_store.insert_vectors(chunks=chunks, vectors=vectors)

        # 6. Update database records
        with get_db_context() as db:
            rec = db.query(IngestionRecord).filter(IngestionRecord.id == ingestion_id).first()
            if rec:
                rec.indexing_status = "indexed"
                rec.indexed_chunks_count = len(chunks)

                # Remove prior chunk records in DB for idempotency
                db.query(LogChunkRecord).filter(LogChunkRecord.ingestion_id == ingestion_id).delete()

                # Persist new chunk records
                chunk_records = [
                    LogChunkRecord(
                        id=c.chunk_id,
                        ingestion_id=ingestion_id,
                        chunk_index=c.chunk_index,
                        service_name=c.service_name,
                        severities_json=json.dumps(c.severities),
                        timestamp_start=c.timestamp_start,
                        timestamp_end=c.timestamp_end,
                        source_line_start=c.source_line_start,
                        source_line_end=c.source_line_end,
                        source_entry_ids_json=json.dumps(c.source_entry_ids),
                        exception_signatures_json=json.dumps(c.exception_signatures),
                        content=c.content,
                    )
                    for c in chunks
                ]
                db.add_all(chunk_records)
                db.commit()

        # Invalidate BM25 in-memory corpus cache to ensure consistency
        from app.retrieval.bm25_search import BM25SearchService

        BM25SearchService.get_instance().invalidate_cache()

        logger.info(
            "Vector indexing completed for ingestion '%s': %d chunks indexed.",
            ingestion_id,
            len(chunks),
        )

        return IndexingResponse(
            ingestion_id=ingestion_id,
            status="indexed",
            indexed_chunks=len(chunks),
            total_log_entries=len(domain_entries),
            original_filename=filename,
            vector_dimension=settings.VECTOR_SIZE,
            collection_name=self.vector_store.collection_name,
            message=f"Successfully indexed {len(chunks)} chunks from {len(domain_entries)} log entries.",
        )

    def get_status(self, ingestion_id: str) -> IndexingStatusResponse:
        """Query current indexing progress and metadata for an ingestion."""
        with get_db_context() as db:
            record = db.query(IngestionRecord).filter(IngestionRecord.id == ingestion_id).first()
            if not record:
                raise AppException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code="INGESTION_NOT_FOUND",
                    message=f"Ingestion '{ingestion_id}' does not exist.",
                )

            return IndexingStatusResponse(
                ingestion_id=record.id,
                status=record.indexing_status,
                indexed_chunks_count=record.indexed_chunks_count,
                total_entries=record.total_entries,
                filename=record.filename,
                created_at=record.created_at,
                updated_at=record.updated_at,
            )

    def search_semantic(self, req: SemanticSearchRequest) -> SemanticSearchResponse:
        """
        Execute semantic similarity retrieval against Qdrant without LLM generation.
        """
        # Generate query vector
        query_vector = self.embedding_service.embed_query(req.query)

        # Retrieve nearest neighbor chunks from Qdrant
        raw_hits = self.vector_store.search(
            query_vector=query_vector,
            top_k=req.top_k,
            service_name=req.service_name,
            severity=req.severity,
            ingestion_id=req.ingestion_id,
        )

        hits: List[SearchResultHit] = []
        for h in raw_hits:
            hits.append(
                SearchResultHit(
                    chunk_id=h["chunk_id"],
                    similarity_score=h["similarity_score"],
                    original_filename=h["original_filename"],
                    relevant_log_content=h["relevant_log_content"],
                    service_name=h.get("service_name"),
                    timestamp_start=h.get("timestamp_start"),
                    timestamp_end=h.get("timestamp_end"),
                    severity=h.get("severity"),
                    source_line_start=h["source_line_start"],
                    source_line_end=h["source_line_end"],
                    source_entry_ids=h.get("source_entry_ids", []),
                    exception_signatures=h.get("exception_signatures", []),
                    metadata=h.get("metadata", {}),
                )
            )

        return SemanticSearchResponse(
            query=req.query,
            total_hits=len(hits),
            hits=hits,
        )

