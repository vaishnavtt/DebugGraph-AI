"""
Qdrant Vector Database Client for DebugGraph AI.
Manages vector collection creation, chunk insertion, deletion, and semantic similarity search.
"""
from typing import Any, Dict, List, Optional
import uuid

from app.core.config import settings
from app.core.logging import get_logger
from app.retrieval.chunking import LogChunk

logger = get_logger(__name__)


class QdrantVectorStore:
    """Manages index operations and vector retrieval against Qdrant."""

    _shared_local_client: Optional[Any] = None

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
        client: Optional[Any] = None,
    ) -> None:
        self.url = url or settings.QDRANT_URL
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self.vector_size = settings.VECTOR_SIZE

        if client is not None:
            self._client = client
        else:
            self._client = None

    def get_client(self):
        """Lazy load or return configured QdrantClient instance."""
        if self._client is not None:
            return self._client

        try:
            from qdrant_client import QdrantClient

            if self.url in (":memory:", "memory"):
                if QdrantVectorStore._shared_local_client is None:
                    QdrantVectorStore._shared_local_client = QdrantClient(location=":memory:")
                self._client = QdrantVectorStore._shared_local_client
                logger.info("Initialized shared in-memory embedded Qdrant client.")
                return self._client

            if self.url.startswith("path://") or self.url in ("local", "embedded"):
                storage_path = (
                    self.url.replace("path://", "") if self.url.startswith("path://") else "qdrant_storage"
                )
                if QdrantVectorStore._shared_local_client is None:
                    QdrantVectorStore._shared_local_client = QdrantClient(path=storage_path)
                self._client = QdrantVectorStore._shared_local_client
                logger.info("Initialized shared local disk-backed embedded Qdrant client at '%s'.", storage_path)
                return self._client

            # If shared local client already active in this process, reuse it directly
            if QdrantVectorStore._shared_local_client is not None:
                self._client = QdrantVectorStore._shared_local_client
                return self._client

            try:
                remote_client = QdrantClient(
                    url=self.url,
                    api_key=self.api_key or None,
                    timeout=1.5,
                )
                # Quick connectivity probe
                remote_client.get_collections()
                self._client = remote_client
                logger.info("Initialized Qdrant client connection to %s", self.url)
            except Exception as conn_err:
                logger.warning(
                    "Remote Qdrant at '%s' is unavailable (%s). Falling back to shared local embedded disk storage at 'qdrant_local_storage'.",
                    self.url,
                    conn_err,
                )
                if QdrantVectorStore._shared_local_client is None:
                    QdrantVectorStore._shared_local_client = QdrantClient(path="qdrant_local_storage")
                self._client = QdrantVectorStore._shared_local_client

        except Exception as exc:
            logger.error("Failed to initialize QdrantClient: %s", exc)
            raise ConnectionError(f"Could not connect to Qdrant at {self.url}: {exc}") from exc

        return self._client

    def ensure_collection(self, collection_name: Optional[str] = None) -> bool:
        """
        Verify collection exists or create with cosine similarity.
        Validates dimensionality if collection already exists to prevent silent mismatch.
        """
        target_collection = collection_name or self.collection_name
        client = self.get_client()

        try:
            from qdrant_client.http.exceptions import UnexpectedResponse
            from qdrant_client.models import Distance, VectorParams
        except ImportError as exc:
            raise RuntimeError("qdrant-client package is required.") from exc

        try:
            exists = client.collection_exists(collection_name=target_collection)
            if exists:
                info = client.get_collection(collection_name=target_collection)
                # Verify vector dimension
                existing_dim = info.config.params.vectors.size
                if existing_dim != self.vector_size:
                    raise ValueError(
                        f"Existing Qdrant collection '{target_collection}' has dimension {existing_dim}, "
                        f"incompatible with required model dimension {self.vector_size}."
                    )
                return False

            client.create_collection(
                collection_name=target_collection,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(
                "Created Qdrant collection '%s' with dimension %d and cosine distance.",
                target_collection,
                self.vector_size,
            )
            return True
        except Exception as exc:
            logger.error("Error ensuring Qdrant collection '%s': %s", target_collection, exc)
            raise

    def get_collection_info(self, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve collection metrics including point count and vector configuration."""
        target_collection = collection_name or self.collection_name
        client = self.get_client()
        try:
            info = client.get_collection(collection_name=target_collection)
            return {
                "collection_name": target_collection,
                "vectors_count": getattr(info, "vectors_count", getattr(info, "points_count", 0)),
                "points_count": getattr(info, "points_count", 0),
                "status": getattr(info, "status", "green"),
                "vector_size": info.config.params.vectors.size,
                "distance": str(info.config.params.vectors.distance),
            }
        except Exception as exc:
            logger.error("Failed to retrieve collection info for '%s': %s", target_collection, exc)
            raise ConnectionError(f"Failed to retrieve Qdrant collection info: {exc}") from exc

    def insert_vectors(
        self,
        chunks: List[LogChunk],
        vectors: List[List[float]],
        collection_name: Optional[str] = None,
    ) -> int:
        """Insert chunk vectors and metadata into Qdrant collection."""
        if not chunks:
            return 0
        if len(chunks) != len(vectors):
            raise ValueError(f"Length mismatch: {len(chunks)} chunks vs {len(vectors)} vectors.")

        target_collection = collection_name or self.collection_name
        client = self.get_client()

        from qdrant_client.models import PointStruct

        points: List[PointStruct] = []
        for chunk, vector in zip(chunks, vectors):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id))
            payload = {
                **chunk.metadata,
                "content": chunk.content,
            }
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            )

        client.upsert(
            collection_name=target_collection,
            points=points,
            wait=True,
        )
        logger.info("Upserted %d vector points into collection '%s'", len(points), target_collection)
        return len(points)

    def delete_by_ingestion_id(
        self,
        ingestion_id: str,
        collection_name: Optional[str] = None,
    ) -> None:
        """Delete all indexed vector points associated with an ingestion (idempotent cleanup)."""
        target_collection = collection_name or self.collection_name
        client = self.get_client()

        from qdrant_client.models import FieldCondition, Filter, MatchValue

        try:
            client.delete(
                collection_name=target_collection,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="ingestion_id",
                            match=MatchValue(value=ingestion_id),
                        )
                    ]
                ),
                wait=True,
            )
            logger.info("Deleted prior vectors for ingestion '%s' from '%s'", ingestion_id, target_collection)
        except Exception as exc:
            logger.warning("Could not delete prior vectors for ingestion '%s': %s", ingestion_id, exc)

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        service_name: Optional[str] = None,
        severity: Optional[str] = None,
        ingestion_id: Optional[str] = None,
        collection_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute semantic similarity search with optional metadata filters.
        """
        target_collection = collection_name or self.collection_name
        client = self.get_client()

        from qdrant_client.models import FieldCondition, Filter, MatchValue

        conditions = []
        if service_name:
            conditions.append(FieldCondition(key="service_name", match=MatchValue(value=service_name)))
        if severity:
            conditions.append(FieldCondition(key="severity", match=MatchValue(value=severity.upper())))
        if ingestion_id:
            conditions.append(FieldCondition(key="ingestion_id", match=MatchValue(value=ingestion_id)))

        query_filter = Filter(must=conditions) if conditions else None

        if hasattr(client, "query_points"):
            response = client.query_points(
                collection_name=target_collection,
                query=query_vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
            )
            scored_points = response.points
        elif hasattr(client, "search"):
            scored_points = client.search(
                collection_name=target_collection,
                query_vector=query_vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
            )
        else:
            raise RuntimeError("Unsupported QdrantClient version: missing query_points/search")

        formatted_hits: List[Dict[str, Any]] = []
        for hit in scored_points:
            payload = hit.payload or {}
            formatted_hits.append(
                {
                    "chunk_id": payload.get("chunk_id", str(hit.id)),
                    "similarity_score": round(float(hit.score), 4),
                    "original_filename": payload.get("original_filename", ""),
                    "relevant_log_content": payload.get("content", ""),
                    "service_name": payload.get("service_name"),
                    "timestamp_start": payload.get("timestamp_start"),
                    "timestamp_end": payload.get("timestamp_end"),
                    "severity": payload.get("severity", "UNKNOWN"),
                    "source_line_start": payload.get("source_line_start", 0),
                    "source_line_end": payload.get("source_line_end", 0),
                    "source_entry_ids": payload.get("source_entry_ids", []),
                    "exception_signatures": payload.get("exception_signatures", []),
                    "metadata": payload,
                }
            )

        return formatted_hits
