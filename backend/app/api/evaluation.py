"""
FastAPI endpoints for DebugGraph AI evaluation and benchmarking.
Provides programmatic access to retrieval comparisons, investigation quality metrics,
ground truth dataset info, and downloadable Markdown reports.
"""
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.logging import get_logger
from app.evaluation.engine import EvaluationEngine, get_evaluation_engine
from app.schemas.evaluation import (
    DatasetInfoResponse,
    EvaluationRunRequest,
    EvaluationRunResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Benchmarks"])


@router.get(
    "/latest",
    response_model=EvaluationRunResponse,
    summary="Get latest evaluation and benchmark results",
)
async def get_latest_evaluation(
    engine: EvaluationEngine = Depends(get_evaluation_engine),
) -> EvaluationRunResponse:
    """
    Retrieves the most recent benchmark evaluation results.
    If no previous run exists, runs an evaluation automatically.
    """
    try:
        return engine.get_latest_results()
    except Exception as exc:
        logger.error("Failed to retrieve latest evaluation results: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load evaluation metrics: {str(exc)}",
        )


@router.post(
    "/run",
    response_model=EvaluationRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger a new evaluation benchmark run",
)
async def trigger_evaluation(
    payload: EvaluationRunRequest,
    engine: EvaluationEngine = Depends(get_evaluation_engine),
) -> EvaluationRunResponse:
    """
    Executes a comprehensive evaluation benchmark measuring:
    1. Retrieval metrics across Dense, BM25, Hybrid RRF, and Cross-Encoder reranking
    2. Investigation fidelity comparing Standard single-pass vs 7-Agent LangGraph workflow
    """
    try:
        return engine.run_benchmark(
            evaluate_retrieval=payload.evaluate_retrieval,
            evaluate_investigation=payload.evaluate_investigation,
            max_queries=payload.max_queries,
        )
    except Exception as exc:
        logger.error("Failed to run evaluation benchmark: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation execution failed: {str(exc)}",
        )


@router.get(
    "/dataset",
    response_model=DatasetInfoResponse,
    summary="Get ground truth benchmark dataset information",
)
async def get_dataset_info(
    engine: EvaluationEngine = Depends(get_evaluation_engine),
) -> DatasetInfoResponse:
    """Returns metadata, categories, and query counts of the benchmark dataset."""
    return engine.get_dataset_info()


@router.get(
    "/reports/{run_id}/markdown",
    response_class=Response,
    summary="Download evaluation report in Markdown format",
)
async def get_markdown_report(
    run_id: str,
    engine: EvaluationEngine = Depends(get_evaluation_engine),
) -> Response:
    """Returns the human-readable Markdown evaluation report."""
    latest = engine.get_latest_results()
    if latest.run_id != run_id and run_id != "latest":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with run_id '{run_id}' not found.",
        )

    return Response(
        content=latest.summary_markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=debuggraph_eval_{run_id}.md"},
    )

