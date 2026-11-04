"""
Pydantic schemas for DebugGraph AI evaluation and benchmarking framework.
Covers retrieval benchmarks (Dense, BM25, Hybrid RRF, Reranker) and
investigation quality metrics (citations, groundedness, category accuracy).
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RetrievalMetrics(BaseModel):
    """Information retrieval evaluation metrics against ground-truth relevant chunks."""

    recall_at_1: float = Field(..., ge=0.0, le=1.0, description="Recall at rank 1")
    recall_at_3: float = Field(..., ge=0.0, le=1.0, description="Recall at rank 3")
    recall_at_5: float = Field(..., ge=0.0, le=1.0, description="Recall at rank 5")
    precision_at_5: float = Field(..., ge=0.0, le=1.0, description="Precision at rank 5")
    mrr: float = Field(..., ge=0.0, le=1.0, description="Mean Reciprocal Rank")
    ndcg_at_5: float = Field(..., ge=0.0, le=1.0, description="Normalized Discounted Cumulative Gain at 5")
    average_latency_ms: float = Field(..., ge=0.0, description="Average query retrieval latency in milliseconds")


class RetrievalMethodComparison(BaseModel):
    """Comparative retrieval performance metrics for a specific search strategy."""

    method: str = Field(..., description="Strategy: 'Dense', 'BM25', 'Hybrid RRF', or 'Hybrid + Reranker'")
    metrics: RetrievalMetrics
    queries_evaluated: int = Field(..., description="Total benchmark queries evaluated")


class InvestigationMetrics(BaseModel):
    """Quality and fidelity metrics for incident investigation reports."""

    citation_precision: float = Field(
        ..., ge=0.0, le=1.0, description="% of cited chunk IDs that are relevant ground-truth evidence"
    )
    citation_recall: float = Field(
        ..., ge=0.0, le=1.0, description="% of ground-truth relevant chunks that were retrieved and cited"
    )
    evidence_groundedness: float = Field(
        ..., ge=0.0, le=1.0, description="Ratio of claims and citations with verifiable backing"
    )
    category_accuracy: float = Field(
        ..., ge=0.0, le=1.0, description="% of cases where diagnosed root-cause matches ground-truth failure domain"
    )
    recommendation_relevance: float = Field(
        ..., ge=0.0, le=1.0, description="% of recommended actions matching domain remediation needs"
    )
    average_latency_ms: float = Field(..., ge=0.0, description="Average investigation duration in milliseconds")


class InvestigationModeComparison(BaseModel):
    """Comparative metrics between Standard investigation and Multi-Agent workflow."""

    mode: str = Field(..., description="'Standard Single-Pass' or 'Multi-Agent LangGraph'")
    metrics: InvestigationMetrics
    average_chunks_retrieved: float = Field(default=0.0)
    average_iterations: float = Field(default=1.0)
    token_usage: Optional[Dict[str, int]] = Field(
        default=None, description="Actual prompt/completion tokens consumed if provided by LLM"
    )


class EvaluationRunRequest(BaseModel):
    """Request payload to execute an automated evaluation run."""

    evaluate_retrieval: bool = Field(default=True, description="Whether to evaluate retrieval methods")
    evaluate_investigation: bool = Field(default=True, description="Whether to evaluate investigation fidelity")
    max_queries: Optional[int] = Field(default=None, description="Optional cap on benchmark queries for quick runs")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "evaluate_retrieval": True,
                "evaluate_investigation": True,
                "max_queries": 15,
            }
        }
    )


class EvaluationRunResponse(BaseModel):
    """Comprehensive evaluation benchmark report."""

    run_id: str = Field(..., description="Unique evaluation execution identifier")
    timestamp: str = Field(..., description="ISO 8601 timestamp of evaluation completion")
    dataset_name: str = Field(..., description="Name of the ground truth benchmark dataset")
    dataset_size: int = Field(..., description="Total ground truth items in the benchmark suite")
    retrieval_comparisons: List[RetrievalMethodComparison] = Field(default_factory=list)
    investigation_comparisons: List[InvestigationModeComparison] = Field(default_factory=list)
    summary_markdown: str = Field(..., description="Human-readable Markdown evaluation report")
    execution_time_seconds: float = Field(..., description="Total benchmark run duration in seconds")


class DatasetInfoResponse(BaseModel):
    """Metadata regarding ground-truth benchmark datasets."""

    dataset_name: str
    total_retrieval_queries: int
    retrieval_categories: List[str]
    sample_queries: List[Dict[str, Any]]
    total_incident_scenarios: int
    incident_categories: List[str]
    description: str

