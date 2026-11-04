"""
Reciprocal Rank Fusion (RRF) for DebugGraph AI.
Merges dense vector retrieval and sparse BM25 keyword retrieval rankings
into a unified ranking based on the RRF mathematical formulation.

Formula:
    RRF(d) = SUM_{m in M} (1 / (k + rank_m(d)))

Note:
    RRF scores represent relative reciprocal rank fusion metrics.
    They are NOT probabilities, confidence scores, or precision measurements.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FusedCandidate:
    """Represents a merged candidate log chunk from multi-method retrieval."""

    chunk_id: str
    rrf_score: float
    retrieval_methods: List[str]
    dense_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    dense_score: Optional[float] = None
    bm25_score: Optional[float] = None
    content: str = ""
    original_filename: str = ""
    service_name: Optional[str] = None
    severity: Optional[str] = None
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    source_line_start: int = 0
    source_line_end: int = 0
    source_entry_ids: List[str] = field(default_factory=list)
    exception_signatures: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert fused candidate to dictionary representation."""
        return {
            "chunk_id": self.chunk_id,
            "rrf_score": self.rrf_score,
            "retrieval_methods": self.retrieval_methods,
            "dense_rank": self.dense_rank,
            "bm25_rank": self.bm25_rank,
            "dense_score": self.dense_score,
            "bm25_score": self.bm25_score,
            "content": self.content,
            "relevant_log_content": self.content,
            "original_filename": self.original_filename,
            "service_name": self.service_name,
            "severity": self.severity,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "source_line_start": self.source_line_start,
            "source_line_end": self.source_line_end,
            "source_entry_ids": self.source_entry_ids,
            "exception_signatures": self.exception_signatures,
            "metadata": self.metadata,
        }


def reciprocal_rank_fusion(
    dense_results: List[Dict[str, Any]],
    sparse_results: List[Dict[str, Any]],
    k: Optional[int] = None,
) -> List[FusedCandidate]:
    """
    Combines dense vector retrieval and sparse BM25 results using Reciprocal Rank Fusion.

    Parameters:
    - dense_results: Ranked list of dictionaries from vector retrieval (with similarity_score).
    - sparse_results: Ranked list of dictionaries from BM25 retrieval (with bm25_score).
    - k: Smoothing constant (default: settings.RRF_K or 60).

    Returns:
    - List of FusedCandidate objects sorted descending by calculated rrf_score.
    """
    rrf_k = k if k is not None else settings.RRF_K
    candidates_by_id: Dict[str, Dict[str, Any]] = {}

    # 1. Process dense retrieval results
    for rank_idx, item in enumerate(dense_results):
        rank = rank_idx + 1  # 1-based ranking
        chunk_id = item.get("chunk_id")
        if not chunk_id:
            continue

        raw_score = item.get("similarity_score")
        dense_score = float(raw_score) if raw_score is not None else None
        rrf_component = 1.0 / (rrf_k + rank)

        candidates_by_id[chunk_id] = {
            "chunk_id": chunk_id,
            "rrf_score": rrf_component,
            "retrieval_methods": ["dense"],
            "dense_rank": rank,
            "bm25_rank": None,
            "dense_score": dense_score,
            "bm25_score": None,
            "content": item.get("relevant_log_content") or item.get("content") or "",
            "original_filename": item.get("original_filename", ""),
            "service_name": item.get("service_name"),
            "severity": item.get("severity"),
            "timestamp_start": item.get("timestamp_start"),
            "timestamp_end": item.get("timestamp_end"),
            "source_line_start": item.get("source_line_start", 0),
            "source_line_end": item.get("source_line_end", 0),
            "source_entry_ids": item.get("source_entry_ids", []),
            "exception_signatures": item.get("exception_signatures", []),
            "metadata": item.get("metadata", {}),
        }

    # 2. Process sparse BM25 retrieval results
    for rank_idx, item in enumerate(sparse_results):
        rank = rank_idx + 1  # 1-based ranking
        chunk_id = item.get("chunk_id")
        if not chunk_id:
            continue

        raw_bm25 = item.get("bm25_score")
        bm25_score = float(raw_bm25) if raw_bm25 is not None else None
        rrf_component = 1.0 / (rrf_k + rank)

        if chunk_id in candidates_by_id:
            # Merge existing dense candidate with BM25 candidate
            cand = candidates_by_id[chunk_id]
            cand["rrf_score"] += rrf_component
            cand["retrieval_methods"].append("bm25")
            cand["bm25_rank"] = rank
            cand["bm25_score"] = bm25_score

            # Enrich missing metadata if sparse candidate has it
            if not cand["content"] and (item.get("content") or item.get("relevant_log_content")):
                cand["content"] = item.get("content") or item.get("relevant_log_content") or ""
            if not cand["original_filename"] and item.get("original_filename"):
                cand["original_filename"] = item.get("original_filename", "")
            if not cand["service_name"] and item.get("service_name"):
                cand["service_name"] = item.get("service_name")
            if not cand["severity"] and item.get("severity"):
                cand["severity"] = item.get("severity")
            if not cand["timestamp_start"] and item.get("timestamp_start"):
                cand["timestamp_start"] = item.get("timestamp_start")
            if not cand["timestamp_end"] and item.get("timestamp_end"):
                cand["timestamp_end"] = item.get("timestamp_end")
            if cand["source_line_start"] == 0 and item.get("source_line_start"):
                cand["source_line_start"] = item.get("source_line_start", 0)
                cand["source_line_end"] = item.get("source_line_end", 0)
            if not cand["exception_signatures"] and item.get("exception_signatures"):
                cand["exception_signatures"] = item.get("exception_signatures", [])
        else:
            # Sparse-only candidate
            candidates_by_id[chunk_id] = {
                "chunk_id": chunk_id,
                "rrf_score": rrf_component,
                "retrieval_methods": ["bm25"],
                "dense_rank": None,
                "bm25_rank": rank,
                "dense_score": None,
                "bm25_score": bm25_score,
                "content": item.get("content") or item.get("relevant_log_content") or "",
                "original_filename": item.get("original_filename", ""),
                "service_name": item.get("service_name"),
                "severity": item.get("severity"),
                "timestamp_start": item.get("timestamp_start"),
                "timestamp_end": item.get("timestamp_end"),
                "source_line_start": item.get("source_line_start", 0),
                "source_line_end": item.get("source_line_end", 0),
                "source_entry_ids": item.get("source_entry_ids", []),
                "exception_signatures": item.get("exception_signatures", []),
                "metadata": item.get("metadata", {}),
            }

    # 3. Build FusedCandidate objects
    fused_list: List[FusedCandidate] = []
    for cand_dict in candidates_by_id.values():
        fused_list.append(
            FusedCandidate(
                chunk_id=cand_dict["chunk_id"],
                rrf_score=round(cand_dict["rrf_score"], 6),
                retrieval_methods=cand_dict["retrieval_methods"],
                dense_rank=cand_dict["dense_rank"],
                bm25_rank=cand_dict["bm25_rank"],
                dense_score=cand_dict["dense_score"],
                bm25_score=cand_dict["bm25_score"],
                content=cand_dict["content"],
                original_filename=cand_dict["original_filename"],
                service_name=cand_dict["service_name"],
                severity=cand_dict["severity"],
                timestamp_start=cand_dict["timestamp_start"],
                timestamp_end=cand_dict["timestamp_end"],
                source_line_start=cand_dict["source_line_start"],
                source_line_end=cand_dict["source_line_end"],
                source_entry_ids=cand_dict["source_entry_ids"],
                exception_signatures=cand_dict["exception_signatures"],
                metadata=cand_dict["metadata"],
            )
        )

    # 4. Sort descending by RRF score; use tie-breaker (dense rank, then bm25 rank)
    def tie_breaker_key(cand: FusedCandidate) -> tuple:
        dense_order = cand.dense_rank if cand.dense_rank is not None else 999999
        bm25_order = cand.bm25_rank if cand.bm25_rank is not None else 999999
        return (cand.rrf_score, -dense_order, -bm25_order)

    fused_list.sort(key=tie_breaker_key, reverse=True)
    return fused_list

