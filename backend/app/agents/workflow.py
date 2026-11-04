"""
LangGraph StateGraph workflow construction and conditional routing logic
for DebugGraph AI multi-agent incident investigations.
"""
from typing import Literal, Optional
from langgraph.graph import END, START, StateGraph

from app.agents.nodes import InvestigationNodes
from app.agents.state import InvestigationState
from app.core.logging import get_logger
from app.graph.manager import KnowledgeGraphManager
from app.retrieval.hybrid_search import HybridSearchEngine
from app.services.gemini_service import GeminiService
from app.services.github_service import GitHubService

logger = get_logger(__name__)


def supervisor_evidence_decision(
    state: InvestigationState,
) -> Literal["retry_retrieval", "proceed_to_resolution", "finalize_insufficient"]:
    """
    Supervisor conditional routing decision:
    Determines whether evidence is sufficient to advance, requires another retrieval iteration,
    or immediately finalizes with an insufficient evidence report.
    """
    validation = state.get("evidence_validation", {})
    is_sufficient = validation.get("is_sufficient", False)
    sufficiency_status = validation.get("sufficiency_status", "INSUFFICIENT")
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 2)
    retrieved_count = len(state.get("retrieved_evidence", []))

    logger.info(
        "Supervisor Decision: sufficiency=%s, is_sufficient=%s, iteration=%d/%d, retrieved=%d",
        sufficiency_status,
        is_sufficient,
        iteration_count,
        max_iterations,
        retrieved_count,
    )

    # 1. Zero evidence retrieved: immediate finalization without looping or resolution
    if retrieved_count == 0:
        logger.info("Supervisor Decision: Zero evidence retrieved. Routing to finalize_insufficient.")
        return "finalize_insufficient"

    # 2. Evidence insufficient or partial, but iterations remain: retry retrieval
    if not is_sufficient and iteration_count < max_iterations:
        logger.info("Supervisor Decision: Evidence insufficient and iterations remain. Routing to retry_retrieval.")
        return "retry_retrieval"

    # 3. Sufficient evidence, or maximum iterations reached: proceed to resolution advisor
    logger.info("Supervisor Decision: Advancing to resolution_advisor.")
    return "proceed_to_resolution"


def create_investigation_graph(
    nodes: Optional[InvestigationNodes] = None,
    hybrid_engine: Optional[HybridSearchEngine] = None,
    gemini_service: Optional[GeminiService] = None,
    graph_manager: Optional[KnowledgeGraphManager] = None,
    github_service: Optional[GitHubService] = None,
) -> StateGraph:
    """
    Assembles and compiles the LangGraph StateGraph workflow coordinating 7 specialized agents:
    START -> supervisor_init -> log_investigator -> graph_investigator -> github_investigator
    -> root_cause_analyst -> evidence_validator -> (conditional router) -> resolution_advisor -> supervisor_finalize -> END
    """
    active_nodes = nodes or InvestigationNodes(
        hybrid_engine=hybrid_engine,
        gemini_service=gemini_service,
        graph_manager=graph_manager,
        github_service=github_service,
    )

    workflow = StateGraph(InvestigationState)

    # Register all 7 specialized agent nodes
    workflow.add_node("supervisor_init", active_nodes.supervisor_init_node)
    workflow.add_node("log_investigator", active_nodes.log_investigator_node)
    workflow.add_node("graph_investigator", active_nodes.graph_investigator_node)
    workflow.add_node("github_investigator", active_nodes.github_investigator_node)
    workflow.add_node("root_cause_analyst", active_nodes.root_cause_analyst_node)
    workflow.add_node("evidence_validator", active_nodes.evidence_validator_node)
    workflow.add_node("resolution_advisor", active_nodes.resolution_advisor_node)
    workflow.add_node("supervisor_finalize", active_nodes.supervisor_finalize_node)

    # Wire standard transitions
    workflow.add_edge(START, "supervisor_init")
    workflow.add_edge("supervisor_init", "log_investigator")
    workflow.add_edge("log_investigator", "graph_investigator")
    workflow.add_edge("graph_investigator", "github_investigator")
    workflow.add_edge("github_investigator", "root_cause_analyst")
    workflow.add_edge("root_cause_analyst", "evidence_validator")

    # Wire conditional supervisor routing
    workflow.add_conditional_edges(
        "evidence_validator",
        supervisor_evidence_decision,
        {
            "retry_retrieval": "log_investigator",
            "proceed_to_resolution": "resolution_advisor",
            "finalize_insufficient": "supervisor_finalize",
        },
    )

    workflow.add_edge("resolution_advisor", "supervisor_finalize")
    workflow.add_edge("supervisor_finalize", END)

    return workflow.compile()

