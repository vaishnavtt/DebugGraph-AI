"""
BM25 Keyword Retrieval Engine for DebugGraph AI.
Indexes persistent log chunks with specialized technical tokenization
and executes keyword retrieval with service and severity filtering.
"""
from dataclasses import dataclass, field
import json
import re
from typing import Any, Dict, List, Optional, Set
from rank_bm25 import BM25Okapi

from app.core.config import settings
from app.core.logging import get_logger
from app.database.models import IngestionRecord, LogChunkRecord
from app.database.session import get_db_context

logger = get_logger(__name__)


def tokenize_log_text(text: str) -> List[str]:
    """
    Tokenizes log text while preserving technical identifiers.
    Preserves:
    - HTTP status codes (e.g. 'HTTP 500' -> 'http_500', 'http', '500')
    - Error codes and hyphenated identifiers (e.g. 'DB-1045', 'payment-service')
    - Dotted classes, modules, and filenames (e.g. 'psycopg2.OperationalError', 'gateway.py')
    - Underscored identifiers (e.g. 'order_id', 'txn_3391')
    - CamelCase / PascalCase exception types (e.g. 'ConnectionTimeoutError')
    - Standard words, numbers, and hex strings.
    """
    if not text:
        return []

    tokens: List[str] = []

    # 1. HTTP Status code patterns like 'HTTP 500', 'HTTP/1.1 500', 'HTTP 404'
    for match in re.finditer(r"\bHTTP(?:/\d(?:\.\d)?)?\s+(\d{3})\b", text, re.IGNORECASE):
        code = match.group(1)
        tokens.append(f"http_{code}")
        tokens.append("http")
        tokens.append(code)

    # 2. Hyphenated technical tokens: e.g. payment-service, DB-1045, bge-small-en-v1.5
    for match in re.finditer(r"\b[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+\b", text):
        full = match.group(0).lower()
        tokens.append(full)
        for part in full.split("-"):
            if part:
                tokens.append(part)

    # 3. Dotted class/module names or file extensions: e.g. psycopg2.OperationalError, gateway.py
    for match in re.finditer(r"\b[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)+\b", text):
        full = match.group(0).lower()
        tokens.append(full)
        for part in full.split("."):
            if part:
                tokens.append(part)

    # 4. Underscore tokens: e.g. order_id, txn_3391, error_code
    for match in re.finditer(r"\b[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+\b", text):
        full = match.group(0).lower()
        tokens.append(full)
        for part in full.split("_"):
            if part:
                tokens.append(part)

    # 5. CamelCase / PascalCase tokens: e.g. ConnectionTimeoutError, GatewayTimeoutException
    for match in re.finditer(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b", text):
        full = match.group(0)
        tokens.append(full.lower())
        subwords = re.findall(r"[A-Z][a-z0-9]*", full)
        for sw in subwords:
            tokens.append(sw.lower())

    # 6. Standard word / number tokens (words, digits, hex)
    for match in re.finditer(r"\b[A-Za-z0-9]+\b", text):
        tokens.append(match.group(0).lower())

    return tokens


@dataclass
class BM25Document:
    """In-memory representation of an indexed log chunk for BM25 retrieval."""

    chunk_id: str
    ingestion_id: str
    original_filename: str
    service_name: Optional[str]
    severities: List[str]
    timestamp_start: Optional[str]
    timestamp_end: Optional[str]
    source_line_start: int
    source_line_end: int
    source_entry_ids: List[str]
    exception_signatures: List[str]
    content: str
    tokens: List[str] = field(default_factory=list)


class BM25SearchService:
    """Service providing BM25 keyword search over persistent log chunk storage."""

    _instance: Optional["BM25SearchService"] = None

    def __init__(self, k1: Optional[float] = None, b: Optional[float] = None) -> None:
        self.k1 = k1 if k1 is not None else settings.BM25_K1
        self.b = b if b is not None else settings.BM25_B
        self._cached_documents: Optional[List[BM25Document]] = None

    @classmethod
    def get_instance(cls) -> "BM25SearchService":
        """Singleton accessor for BM25 search service."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def invalidate_cache(self) -> None:
        """Invalidates cached corpus when new logs are ingested or removed."""
        self._cached_documents = None
        logger.info("BM25 in-memory corpus cache invalidated.")

    def _load_documents(self) -> List[BM25Document]:
        """Loads and tokenizes all persistent log chunks from database."""
        if self._cached_documents is not None:
            return self._cached_documents

        with get_db_context() as db:
            query = (
                db.query(LogChunkRecord, IngestionRecord.filename)
                .join(IngestionRecord, LogChunkRecord.ingestion_id == IngestionRecord.id)
                .order_by(LogChunkRecord.created_at.asc())
            )
            rows = query.all()

            documents: List[BM25Document] = []
            for chunk_rec, filename in rows:
                severities: List[str] = []
                if chunk_rec.severities_json:
                    try:
                        severities = json.loads(chunk_rec.severities_json)
                    except Exception:
                        severities = []

                source_entry_ids: List[str] = []
                if chunk_rec.source_entry_ids_json:
                    try:
                        source_entry_ids = json.loads(chunk_rec.source_entry_ids_json)
                    except Exception:
                        source_entry_ids = []

                exception_signatures: List[str] = []
                if chunk_rec.exception_signatures_json:
                    try:
                        exception_signatures = json.loads(chunk_rec.exception_signatures_json)
                    except Exception:
                        exception_signatures = []

                tokens = tokenize_log_text(chunk_rec.content)

                documents.append(
                    BM25Document(
                        chunk_id=chunk_rec.id,
                        ingestion_id=chunk_rec.ingestion_id,
                        original_filename=filename,
                        service_name=chunk_rec.service_name,
                        severities=severities,
                        timestamp_start=chunk_rec.timestamp_start.isoformat() if chunk_rec.timestamp_start else None,
                        timestamp_end=chunk_rec.timestamp_end.isoformat() if chunk_rec.timestamp_end else None,
                        source_line_start=chunk_rec.source_line_start,
                        source_line_end=chunk_rec.source_line_end,
                        source_entry_ids=source_entry_ids,
                        exception_signatures=exception_signatures,
                        content=chunk_rec.content,
                        tokens=tokens,
                    )
                )

            self._cached_documents = documents
            logger.info("Loaded and tokenized %d log chunks into BM25 corpus.", len(documents))
            return self._cached_documents

    def search(
        self,
        query: str,
        top_k: int = 5,
        service_name: Optional[str] = None,
        severity: Optional[str] = None,
        ingestion_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes BM25 keyword search over indexed log chunks.

        Returns ranked results with:
        - chunk_id
        - bm25_score (BM25Okapi relevance score)
        - original_filename
        - content
        - service_name
        - severity
        - timestamp_start, timestamp_end
        - source_line_start, source_line_end
        - source_entry_ids, exception_signatures
        - metadata
        """
        stripped_query = query.strip()
        if not stripped_query:
            return []

        all_docs = self._load_documents()
        if not all_docs:
            return []

        # Apply metadata filters
        filtered_docs: List[BM25Document] = []
        for doc in all_docs:
            if ingestion_id and doc.ingestion_id != ingestion_id:
                continue
            if service_name and doc.service_name != service_name:
                continue
            if severity and severity.upper() not in [s.upper() for s in doc.severities]:
                continue
            filtered_docs.append(doc)

        if not filtered_docs:
            return []

        query_tokens = tokenize_log_text(stripped_query)
        if not query_tokens:
            return []

        tokenized_corpus = [doc.tokens for doc in filtered_docs]
        bm25 = BM25Okapi(tokenized_corpus, k1=self.k1, b=self.b)

        # Standard Lucene-style non-negative IDF floor to prevent negative scores
        # for terms appearing in >= 50% of candidate documents or single-document subsets.
        for word, idf_val in list(bm25.idf.items()):
            if idf_val <= 0:
                bm25.idf[word] = 0.25

        scores = bm25.get_scores(query_tokens)

        # Pair candidates with BM25 score and filter for positive relevance
        scored_candidates = []
        for doc, score in zip(filtered_docs, scores):
            if score > 0.0:
                scored_candidates.append((doc, float(score)))

        # Sort descending by BM25 score
        scored_candidates.sort(key=lambda pair: pair[1], reverse=True)
        top_candidates = scored_candidates[:top_k]

        results: List[Dict[str, Any]] = []
        for doc, score in top_candidates:
            primary_severity = doc.severities[0] if doc.severities else "UNKNOWN"
            results.append(
                {
                    "chunk_id": doc.chunk_id,
                    "bm25_score": round(score, 4),
                    "original_filename": doc.original_filename,
                    "content": doc.content,
                    "relevant_log_content": doc.content,
                    "service_name": doc.service_name,
                    "timestamp_start": doc.timestamp_start,
                    "timestamp_end": doc.timestamp_end,
                    "severity": primary_severity,
                    "severities": doc.severities,
                    "source_line_start": doc.source_line_start,
                    "source_line_end": doc.source_line_end,
                    "source_entry_ids": doc.source_entry_ids,
                    "exception_signatures": doc.exception_signatures,
                    "metadata": {
                        "chunk_id": doc.chunk_id,
                        "ingestion_id": doc.ingestion_id,
                        "original_filename": doc.original_filename,
                        "service_name": doc.service_name,
                        "severity": primary_severity,
                        "source_line_start": doc.source_line_start,
                        "source_line_end": doc.source_line_end,
                        "timestamp_start": doc.timestamp_start,
                        "timestamp_end": doc.timestamp_end,
                    },
                }
            )

        return results
