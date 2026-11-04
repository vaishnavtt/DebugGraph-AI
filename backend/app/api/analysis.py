"""
Incident Analysis API endpoints for DebugGraph AI.
Provides evidence-grounded incident investigation powered by hybrid retrieval and Google Gemini LLM.
"""
from fastapi import APIRouter, Depends, status

from app.core.logging import get_logger
from app.schemas.investigation import (
    AgenticInvestigationResponse,
    InvestigationRequest,
    InvestigationResponse,
)
from app.services.agentic_investigation_service import AgenticInvestigationService
from app.services.incident_investigation_service import IncidentInvestigationService

logger = get_logger(__name__)

router = APIRouter(prefix="/analysis", tags=["Incident Analysis"])


def get_investigation_service() -> IncidentInvestigationService:
    """Dependency provider for IncidentInvestigationService."""
    return IncidentInvestigationService()


def get_agentic_investigation_service() -> AgenticInvestigationService:
    """Dependency provider for AgenticInvestigationService."""
    return AgenticInvestigationService()


@router.post(
    "/investigate",
    response_model=InvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evidence-Grounded Incident Investigation",
    description=(
        "Executes end-to-end incident root cause analysis. Retrieves log evidence using "
        "hybrid search (dense vectors + BM25 keyword + RRF + Cross-Encoder reranking), "
        "prepares delimited evidence context, and uses Google Gemini to generate a structured, "
        "evidence-grounded incident report with strict citation validation."
    ),
)
async def investigate_incident(
    request: InvestigationRequest,
    service: IncidentInvestigationService = Depends(get_investigation_service),
) -> InvestigationResponse:
    """
    Investigate an incident based on natural language symptoms or error inquiries.

    - **query**: Description of incident or error (e.g., 'Why is the payment service failing?')
    - **top_k**: Number of top evidence chunks to retrieve and analyze (default: 10)
    - **service_name**: Optional filter to restrict retrieval to a specific service
    - **severity**: Optional filter for log severity level (e.g., 'ERROR')
    - **ingestion_id**: Optional filter for a specific log ingestion batch
    - **rerank**: Whether to execute Cross-Encoder reranking (default: True)
    """
    logger.info("Received incident investigation request for query: '%s'", request.query)
    response = await service.investigate(request)
    return response


@router.post(
    "/investigate/agentic",
    response_model=AgenticInvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="LangGraph Multi-Agent Incident Investigation",
    description=(
        "Executes a coordinated multi-agent incident investigation using LangGraph. "
        "Coordinates five specialized agents: SupervisorAgent, LogInvestigatorAgent, "
        "RootCauseAnalystAgent, EvidenceValidatorAgent, and ResolutionAdvisorAgent. "
        "Enforces strict citation grounding, conditional retry loops, and safety warnings."
    ),
)
async def investigate_incident_agentic(
    request: InvestigationRequest,
    service: AgenticInvestigationService = Depends(get_agentic_investigation_service),
) -> AgenticInvestigationResponse:
    """
    Execute a LangGraph multi-agent investigation workflow for an incident inquiry.

    - **query**: Description of incident or error (e.g., 'Why is the payment service failing?')
    - **top_k**: Number of top evidence chunks to retrieve and analyze (default: 10)
    - **service_name**: Optional filter to restrict retrieval to a specific service
    - **severity**: Optional filter for log severity level (e.g., 'ERROR')
    - **ingestion_id**: Optional filter for a specific log ingestion batch
    - **rerank**: Whether to execute Cross-Encoder reranking (default: True)
    """
    logger.info("Received agentic incident investigation request for query: '%s'", request.query)
    response = await service.investigate(request)
    return response

