"""
Agentic Investigation Service for DebugGraph AI.
Orchestrates multi-agent incident investigations powered by LangGraph,
linking specialized agents for retrieval, root cause analysis, citation validation,
and resolution planning.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

from app.agents.nodes import InvestigationNodes
from app.agents.state import InvestigationState
from app.agents.workflow import create_investigation_graph
from app.core.logging import get_logger
from app.graph.manager import KnowledgeGraphManager
from app.retrieval.hybrid_search import HybridSearchEngine
from app.schemas.investigation import (
    AgentExecutionStep,
    AgenticInvestigationResponse,
    EvidenceSufficiency,
    FurtherInvestigation,
    InvestigationRequest,
    ModelInformation,
)
from app.services.gemini_service import GeminiService
from app.services.github_service import GitHubService

logger = get_logger(__name__)


class AgenticInvestigationService:
    """
    Executes multi-agent incident investigations using a compiled LangGraph workflow.
    """

    def __init__(
        self,
        hybrid_engine: Optional[HybridSearchEngine] = None,
        gemini_service: Optional[GeminiService] = None,
        graph_manager: Optional[KnowledgeGraphManager] = None,
        github_service: Optional[GitHubService] = None,
        nodes: Optional[InvestigationNodes] = None,
    ) -> None:
        self.hybrid_engine = hybrid_engine or HybridSearchEngine()
        self.gemini_service = gemini_service or GeminiService()
        self.graph_manager = graph_manager or KnowledgeGraphManager()
        self.github_service = github_service or GitHubService()
        self.nodes = nodes or InvestigationNodes(
            hybrid_engine=self.hybrid_engine,
            gemini_service=self.gemini_service,
            graph_manager=self.graph_manager,
            github_service=self.github_service,
        )
        self.graph = create_investigation_graph(nodes=self.nodes)

    async def investigate(
        self,
        request: InvestigationRequest,
    ) -> AgenticInvestigationResponse:
        """
        Executes the LangGraph multi-agent investigation workflow for the incoming request.

        Parameters:
        - request: InvestigationRequest with query, top_k, and optional filters.

        Returns:
        - Validated AgenticInvestigationResponse model.
        """
        investigation_id = f"inv_agent_{uuid.uuid4().hex[:12]}"
        logger.info(
            "Starting agentic multi-agent investigation [%s] for query: '%s'",
            investigation_id,
            request.query,
        )

        initial_state: InvestigationState = {
            "investigation_id": investigation_id,
            "query": request.query,
            "top_k": request.top_k,
            "service_name": request.service_name,
            "severity": request.severity,
            "ingestion_id": request.ingestion_id,
            "rerank": request.rerank,
            "iteration_count": 0,
            "max_iterations": 2,
            "investigation_status": "INITIALIZED",
            "errors": [],
            "retrieved_evidence": [],
            "log_findings": {},
            "graph_evidence": None,
            "github_evidence": None,
            "blast_radius": None,
            "root_cause_hypotheses": [],
            "evidence_validation": {},
            "recommended_actions": [],
            "agent_execution_trace": [],
            "final_report": None,
        }

        try:
            final_state: InvestigationState = await self.graph.ainvoke(initial_state)
        except Exception as exc:
            logger.error("LangGraph agentic execution error [%s]: %s", investigation_id, exc, exc_info=True)
            return self._build_failed_response(
                investigation_id=investigation_id,
                query=request.query,
                error_message=str(exc),
            )

        final_report = final_state.get("final_report")
        if not final_report:
            logger.warning("LangGraph returned without final_report for [%s]", investigation_id)
            return self._build_failed_response(
                investigation_id=investigation_id,
                query=request.query,
                error_message="Workflow finished without generating a final report.",
            )

        return AgenticInvestigationResponse.model_validate(final_report)

    def _build_failed_response(
        self,
        investigation_id: str,
        query: str,
        error_message: str,
    ) -> AgenticInvestigationResponse:
        """Constructs a deterministic failure response when the graph raises an unhandled exception."""
        failed_trace = [
            AgentExecutionStep(
                agent_name="SupervisorAgent",
                stage="workflow_exception",
                status="FAILED",
                timestamp=datetime.now(timezone.utc).isoformat(),
                summary=f"Workflow failed: {error_message}",
                latency_ms=0.0,
            )
        ]
        model_name = getattr(self.gemini_service, "model_name", "gemini-flash-latest")
        if not isinstance(model_name, str):
            model_name = "gemini-flash-latest"

        return AgenticInvestigationResponse(
            investigation_id=investigation_id,
            query=query,
            incident_summary=f"The multi-agent investigation encountered a fatal workflow exception: {error_message}",
            affected_services=[],
            severity_assessment="UNKNOWN",
            key_observations=[],
            potential_root_causes=[],
            supporting_evidence=[],
            recommended_actions=[],
            further_investigation=FurtherInvestigation(
                missing_evidence=["Agent diagnostic logs"],
                recommended_checks=["Inspect backend error logs and retry investigation."],
            ),
            evidence_sufficiency=EvidenceSufficiency(
                status="INSUFFICIENT",
                reason=f"Workflow aborted: {error_message}",
                confidence_score=0.0,
            ),
            model_information=ModelInformation(
                model_name=model_name,
                provider="Google Gemini (LangGraph Multi-Agent)",
            ),
            retrieved_chunks_count=0,
            created_at=datetime.now(timezone.utc).isoformat(),
            workflow_status="FAILED",
            iterations_executed=1,
            agent_execution_trace=failed_trace,
        )
