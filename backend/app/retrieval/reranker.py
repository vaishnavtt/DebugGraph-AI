"""
Cross-Encoder Reranking Module for DebugGraph AI.
Applies BAAI/bge-reranker-base to calculate precise query-document relevance logits
and reorder fused candidate log chunks.

Important:
    Raw reranker outputs are uncalibrated relevance logits (cross-encoder score).
    They must NOT be interpreted as probabilities or percentages.
"""
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.retrieval.fusion import FusedCandidate

logger = get_logger(__name__)


class CrossEncoderReranker:
    """Manages lazy loading and batch inference for the BGE cross-encoder reranking model."""

    _instance: Optional["CrossEncoderReranker"] = None

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        model: Optional[Any] = None,
    ) -> None:
        self.model_name = model_name or settings.RERANKER_MODEL
        self.device = device or settings.RERANKER_DEVICE
        self._model = model

    @classmethod
    def get_instance(cls) -> "CrossEncoderReranker":
        """Singleton accessor to guarantee model weights are loaded at most once."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_instance(cls, instance: Optional["CrossEncoderReranker"]) -> None:
        """Allows test suites to register deterministic mock reranker instances."""
        cls._instance = instance

    def _get_model(self) -> Any:
        """Lazily initialize the CrossEncoder model."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder

                logger.info(
                    "Loading CrossEncoder model '%s' on device '%s'...",
                    self.model_name,
                    self.device,
                )
                self._model = CrossEncoder(
                    model_name=self.model_name,
                    device=self.device,
                )
                logger.info("CrossEncoder model '%s' loaded successfully.", self.model_name)
            except Exception as exc:
                logger.error("Failed to load CrossEncoder model '%s': %s", self.model_name, exc)
                raise RuntimeError(f"Could not initialize CrossEncoder model '{self.model_name}': {exc}") from exc
        return self._model

    def rerank(
        self,
        query: str,
        candidates: Sequence[Union[FusedCandidate, Dict[str, Any]]],
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate documents against the query.

        Parameters:
        - query: The technical or natural language search query.
        - candidates: Sequence of FusedCandidate or dict objects containing 'content' / 'chunk_id'.
        - top_k: Maximum number of reranked candidates to return. If None, returns all.

        Returns:
        - List of candidates converted to dict, sorted descending by reranker_score.
        """
        if not candidates:
            return []

        stripped_query = query.strip()
        if not stripped_query:
            # If query is empty, return candidates in existing order
            results = [c.to_dict() if isinstance(c, FusedCandidate) else dict(c) for c in candidates]
            return results[:top_k] if top_k else results

        # Normalize candidates to mutable dictionaries
        candidate_dicts: List[Dict[str, Any]] = [
            c.to_dict() if isinstance(c, FusedCandidate) else dict(c) for c in candidates
        ]

        pairs: List[Tuple[str, str]] = [
            (stripped_query, c.get("content") or c.get("relevant_log_content") or "") for c in candidate_dicts
        ]

        try:
            model = self._get_model()
            raw_scores = model.predict(pairs)

            # Convert numpy array / tensor to float list
            if isinstance(raw_scores, np.ndarray):
                scores_list = [float(s) for s in raw_scores.tolist()]
            elif isinstance(raw_scores, (list, tuple)):
                scores_list = [float(s) for s in raw_scores]
            else:
                scores_list = [float(raw_scores)]

            for cand, score in zip(candidate_dicts, scores_list):
                cand["reranker_score"] = round(score, 4)

            # Sort descending by reranker_score
            candidate_dicts.sort(key=lambda c: c.get("reranker_score", -999999.0), reverse=True)

        except Exception as exc:
            logger.warning(
                "Cross-encoder inference failed for query '%s' (%s). Retaining original fusion order.",
                stripped_query,
                exc,
            )
            for cand in candidate_dicts:
                cand.setdefault("reranker_score", None)

        if top_k is not None and top_k > 0:
            return candidate_dicts[:top_k]
        return candidate_dicts

