"""
Retrieval Benchmark Suite for DebugGraph AI (Phase 5).
Evaluates retrieval performance across:
A. Dense vector retrieval only
B. BM25 keyword retrieval only
C. Hybrid retrieval with Reciprocal Rank Fusion (RRF)
D. Hybrid retrieval with Cross-Encoder reranking (BAAI/bge-reranker-base)

Calculates Recall@5, Precision@5, MRR@5, and NDCG@5 against known ground truth chunk relevance.
"""
from dataclasses import dataclass
import json
import math
import os
import sys
from typing import Any, Dict, List, Set

# Ensure backend root is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.core.logging import get_logger
from app.database.models import IngestionRecord, LogChunkRecord
from app.database.session import get_db_context, init_db
from app.retrieval.bm25_search import BM25SearchService
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.hybrid_search import HybridSearchEngine
from app.retrieval.reranker import CrossEncoderReranker
from app.retrieval.vector_store import QdrantVectorStore
from app.services.log_ingestion_service import LogIngestionService
from app.services.vector_indexing_service import VectorIndexingService

logger = get_logger(__name__)


@dataclass
class BenchmarkQuery:
    query_id: str
    category: str
    query: str
    relevant_keywords: List[str]  # Ground truth keywords that identify relevant chunk content


BENCHMARK_QUERIES: List[BenchmarkQuery] = [
    # 1. Exact Error Code Queries
    BenchmarkQuery("Q01", "Exact Error Code", "HTTP 500 DB-1045", ["DB-1045", "Access denied for user 'admin'"]),
    BenchmarkQuery("Q02", "Exact Error Code", "DB-1045", ["DB-1045", "mysql_client.connect"]),
    BenchmarkQuery("Q03", "Exact Error Code", "exit code 137", ["exit code 137", "OOMKilled"]),
    BenchmarkQuery("Q04", "Exact Error Code", "HTTP 401 Unauthorized", ["HTTP 401", "InvalidSignatureError"]),
    BenchmarkQuery("Q05", "Exact Error Code", "HTTP 503 Service Unavailable", ["HTTP 503", "NullPointerException"]),
    BenchmarkQuery("Q06", "Exact Error Code", "Errno 98 Address already in use", ["Errno 98", "port 8080"]),
    # 2. Semantic Queries
    BenchmarkQuery(
        "Q07",
        "Semantic",
        "Why are payment checkout transactions timing out?",
        ["ConnectionTimeoutError", "payment gateway timed out after 5000ms"],
    ),
    BenchmarkQuery(
        "Q08",
        "Semantic",
        "Database connection exhaustion during high load",
        ["PoolTimeoutError", "Queue pool limit of size 50 overflow 10 reached"],
    ),
    BenchmarkQuery(
        "Q09",
        "Semantic",
        "User authentication token signature validation failures",
        ["InvalidSignatureError", "JWT signature verification failed"],
    ),
    BenchmarkQuery(
        "Q10",
        "Semantic",
        "Order checkout stock reservation issues",
        ["Reserving stock inventory", "ord_9901"],
    ),
    BenchmarkQuery(
        "Q11",
        "Semantic",
        "Container pod crashing repeatedly after deployment",
        ["CrashLoopBackOff", "restarting failed container web-app"],
    ),
    BenchmarkQuery(
        "Q12",
        "Semantic",
        "High latency and provider delays on checkout",
        ["Upstream payment provider latency spike", "1240ms"],
    ),
    # 3. Service-Specific Queries
    BenchmarkQuery(
        "Q13",
        "Service-Specific",
        "payment-service circuit breaker tripped for Stripe",
        ["Circuit breaker tripped for StripeClient", "OPEN circuit state"],
    ),
    BenchmarkQuery(
        "Q14",
        "Service-Specific",
        "database-service deadlock detected on transaction log",
        ["Deadlock detected on lock key transaction_log_pkey", "pid=4810"],
    ),
    BenchmarkQuery(
        "Q15",
        "Service-Specific",
        "auth-service identity and session token refresh",
        ["Identity and Access Management service started", "User session token refreshed"],
    ),
    BenchmarkQuery(
        "Q16",
        "Service-Specific",
        "order-service Java heap space memory leak",
        ["java.lang.OutOfMemoryError: Java heap space", "JVM terminated unexpectedly"],
    ),
    BenchmarkQuery(
        "Q17",
        "Service-Specific",
        "k8s-deployment readiness probe healthcheck failure",
        ["Readiness probe failed HTTP 500", "gateway healthcheck returned unhealthy"],
    ),
    BenchmarkQuery(
        "Q18",
        "Service-Specific",
        "payment-service routing transactions to fallback provider Braintree",
        ["Routing fallback transactions to secondary provider Braintree", "Fallback route established"],
    ),
    # 4. Stack Trace & Exception Queries
    BenchmarkQuery(
        "Q19",
        "Stack Trace",
        "ConnectionTimeoutError Connection to payment gateway timed out after 5000ms",
        ["ConnectionTimeoutError", "stripe_client.py"],
    ),
    BenchmarkQuery(
        "Q20",
        "Stack Trace",
        "PoolTimeoutError Queue pool limit of size 50 overflow 10 reached",
        ["PoolTimeoutError", "pool.py"],
    ),
    BenchmarkQuery(
        "Q21",
        "Stack Trace",
        "NullPointerException in OrderValidator.java validateOrder",
        ["NullPointerException", "OrderValidator.java"],
    ),
    BenchmarkQuery(
        "Q22",
        "Stack Trace",
        "psycopg2.OperationalError server closed the connection unexpectedly",
        ["psycopg2.OperationalError", "connection reset by peer"],
    ),
    BenchmarkQuery(
        "Q23",
        "Stack Trace",
        "InvalidSignatureError Signature verification failed key ID mismatch",
        ["InvalidSignatureError", "key ID mismatch"],
    ),
    BenchmarkQuery(
        "Q24",
        "Stack Trace",
        "OSError Address already in use failed to bind socket on port 8080",
        ["failed to bind socket on port 8080", "OSError"],
    ),
    # 5. Database Failure Queries
    BenchmarkQuery(
        "Q25",
        "Database Failure",
        "PostgreSQL connection pool initialized with min_size=10",
        ["PostgreSQL connection pool initialized with min_size=10", "ping latency 1.4ms"],
    ),
    BenchmarkQuery(
        "Q26",
        "Database Failure",
        "Slow query detected duration 3420ms SELECT FOR UPDATE",
        ["Slow query detected: duration=3420ms", "SELECT * FROM orders WHERE status = 'PENDING' FOR UPDATE"],
    ),
    BenchmarkQuery(
        "Q27",
        "Database Failure",
        "Transaction rolled back due to deadlock between pid=4810 and pid=4812",
        ["Deadlock detected on lock key transaction_log_pkey", "Transaction rolled back for session_id=sess_7719"],
    ),
    BenchmarkQuery(
        "Q28",
        "Database Failure",
        "Purged idle connections to reclaim database pool capacity",
        ["Purged 8 idle connections to reclaim pool capacity", "replication lag 0.2s"],
    ),
    BenchmarkQuery(
        "Q29",
        "Database Failure",
        "MySQL Access denied for user admin localhost using password YES",
        ["DB-1045 Access denied for user 'admin'@'localhost'", "mysql_client.connect"],
    ),
    # 6. Deployment & Infrastructure Queries
    BenchmarkQuery(
        "Q30",
        "Deployment",
        "CrashLoopBackOff back-off 5m0s restarting failed container",
        ["CrashLoopBackOff", "restarting failed container web-app"],
    ),
    BenchmarkQuery(
        "Q31",
        "Deployment",
        "OOMKilled memory limit 512Mi exceeded",
        ["OOMKilled exit code 137", "memory limit 512Mi exceeded"],
    ),
    BenchmarkQuery(
        "Q32",
        "Deployment",
        "Removing pod from service endpoint routing table",
        ["Removing pod web-app-deployment", "endpoint routing table"],
    ),
]


def calculate_metrics(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int = 5) -> Dict[str, float]:
    """Calculate Recall@k, Precision@k, MRR@k, and NDCG@k."""
    top_k_ids = retrieved_ids[:k]
    if not top_k_ids or not ground_truth_ids:
        return {"recall": 0.0, "precision": 0.0, "mrr": 0.0, "ndcg": 0.0}

    hits = [1 if cid in ground_truth_ids else 0 for cid in top_k_ids]
    num_hits = sum(hits)

    recall = num_hits / len(ground_truth_ids) if ground_truth_ids else 0.0
    precision = num_hits / k

    # MRR@k: reciprocal rank of the first hit
    mrr = 0.0
    for idx, hit in enumerate(hits):
        if hit == 1:
            mrr = 1.0 / (idx + 1)
            break

    # NDCG@k: DCG / IDCG
    dcg = sum(hit / math.log2(idx + 2) for idx, hit in enumerate(hits))
    ideal_hits = [1] * min(len(ground_truth_ids), k)
    idcg = sum(1.0 / math.log2(idx + 2) for idx in range(len(ideal_hits)))
    ndcg = (dcg / idcg) if idcg > 0 else 0.0

    return {
        "recall": recall,
        "precision": precision,
        "mrr": mrr,
        "ndcg": ndcg,
    }


def run_benchmark():
    """Execute complete retrieval benchmark comparing all 4 strategies."""
    init_db()
    eval_log_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "datasets", "evaluation", "eval_logs.log")
    )
    if not os.path.exists(eval_log_path):
        raise FileNotFoundError(f"Evaluation logs file not found at {eval_log_path}")

    # Read log content
    with open(eval_log_path, "r", encoding="utf-8") as f:
        log_bytes = f.read().encode("utf-8")

    # Ingest and Index
    ingestion_service = LogIngestionService()
    ingestion_result = ingestion_service.process_log_upload(
        raw_bytes=log_bytes,
        original_filename="eval_logs.log",
    )
    ingestion_id = ingestion_result.ingestion_id
    logger.info("Ingestion completed: ID %s with %d parsed entries.", ingestion_id, ingestion_result.total_entries)

    vector_store = QdrantVectorStore()
    vector_indexing_service = VectorIndexingService(vector_store=vector_store)
    vector_indexing_service.index_ingestion(ingestion_id)
    logger.info("Vector indexing completed into Qdrant & database.")

    # Load all indexed chunks to determine ground truth chunk IDs
    with get_db_context() as db:
        chunk_records = (
            db.query(LogChunkRecord).filter(LogChunkRecord.ingestion_id == ingestion_id).all()
        )

    chunk_map: Dict[str, str] = {c.id: c.content for c in chunk_records}
    logger.info("Loaded %d chunk records for ground truth mapping.", len(chunk_map))

    # Map queries to ground truth chunk IDs
    query_ground_truth: Dict[str, Set[str]] = {}
    for bq in BENCHMARK_QUERIES:
        matching_chunks = set()
        for cid, content in chunk_map.items():
            for kw in bq.relevant_keywords:
                if kw.lower() in content.lower():
                    matching_chunks.add(cid)
                    break
        query_ground_truth[bq.query_id] = matching_chunks

    # Initialize retrieval engines
    hybrid_engine = HybridSearchEngine(vector_store=vector_store)
    bm25_service = BM25SearchService.get_instance()
    embedding_service = EmbeddingService.get_instance()

    reranker = hybrid_engine.reranker

    methods = ["A_Dense_Only", "B_BM25_Only", "C_Hybrid_RRF", "D_Hybrid_RRF_Reranker"]
    metrics_by_method = {m: {"recall": [], "precision": [], "mrr": [], "ndcg": []} for m in methods}

    print(f"\n================================================================================", flush=True)
    print(f"BENCHMARKING RETRIEVAL ENGINE ACROSS {len(BENCHMARK_QUERIES)} TECHNICAL QUERIES", flush=True)
    print(f"================================================================================", flush=True)

    for idx, bq in enumerate(BENCHMARK_QUERIES):
        gt_ids = query_ground_truth[bq.query_id]
        if not gt_ids:
            continue

        query_str = bq.query

        # 1. Dense Semantic Retrieval (top 20 candidates)
        q_vec = embedding_service.embed_query(query_str)
        dense_candidates = vector_store.search(
            query_vector=q_vec,
            top_k=20,
            ingestion_id=ingestion_id,
        )

        # 2. Sparse BM25 Retrieval (top 20 candidates)
        sparse_candidates = bm25_service.search(
            query=query_str,
            top_k=20,
            ingestion_id=ingestion_id,
        )

        # Method A: Dense Retrieval only (top 5)
        dense_top5_ids = [h["chunk_id"] for h in dense_candidates[:5]]

        # Method B: BM25 only (top 5)
        bm25_top5_ids = [h["chunk_id"] for h in sparse_candidates[:5]]

        # Method C: Hybrid RRF only (top 5)
        fused_candidates = reciprocal_rank_fusion(
            dense_results=dense_candidates,
            sparse_results=sparse_candidates,
            k=settings.RRF_K,
        )
        rrf_top5_ids = [c.chunk_id for c in fused_candidates[:5]]

        # Method D: Hybrid RRF + Cross-Encoder Reranker (top 5)
        reranked_dicts = reranker.rerank(
            query=query_str,
            candidates=fused_candidates[:20],
            top_k=5,
        )
        rerank_top5_ids = [c["chunk_id"] for c in reranked_dicts]

        # Calculate metrics for each method
        for m_name, retrieved in [
            ("A_Dense_Only", dense_top5_ids),
            ("B_BM25_Only", bm25_top5_ids),
            ("C_Hybrid_RRF", rrf_top5_ids),
            ("D_Hybrid_RRF_Reranker", rerank_top5_ids),
        ]:
            res = calculate_metrics(retrieved, gt_ids, k=5)
            for metric in ["recall", "precision", "mrr", "ndcg"]:
                metrics_by_method[m_name][metric].append(res[metric])

        print(
            f"  [{idx+1:02d}/{len(BENCHMARK_QUERIES)}] [{bq.category:<16}] {bq.query_id}: '{bq.query[:38]:<38}' "
            f"-> RRF Top: {rrf_top5_ids[0] if rrf_top5_ids else 'None'}",
            flush=True,
        )

    # Compute averages
    summary_results: Dict[str, Dict[str, float]] = {}
    print(f"\n{'-' * 80}", flush=True)
    print(
        f"{'Retrieval Strategy':<30} | {'Recall@5':<10} | {'Precision@5':<12} | {'MRR@5':<10} | {'NDCG@5':<10}",
        flush=True,
    )
    print(f"{'-' * 80}", flush=True)

    for m_name in methods:
        summary_results[m_name] = {}
        for metric in ["recall", "precision", "mrr", "ndcg"]:
            vals = metrics_by_method[m_name][metric]
            summary_results[m_name][metric] = round(sum(vals) / len(vals), 4) if vals else 0.0

        print(
            f"{m_name:<30} | "
            f"{summary_results[m_name]['recall']:<10.4f} | "
            f"{summary_results[m_name]['precision']:<12.4f} | "
            f"{summary_results[m_name]['mrr']:<10.4f} | "
            f"{summary_results[m_name]['ndcg']:<10.4f}",
            flush=True,
        )

    print(f"{'-' * 80}\n", flush=True)

    # Persist benchmark results to JSON
    results_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "datasets", "evaluation", "benchmark_results.json")
    )
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(summary_results, f, indent=2)
    logger.info("Saved benchmark metrics to %s", results_path)
    return summary_results


if __name__ == "__main__":
    run_benchmark()
