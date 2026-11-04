"""
Investigation State definition for LangGraph multi-agent workflows.
Enforces typed state transitions across specialized investigation agents.
"""
from typing import Any, Dict, List, Optional, TypedDict


class InvestigationState(TypedDict, total=False):
    """
    Shared investigation state mutated across LangGraph agent nodes.
    Each agent reads from and modifies only its authorized state fields.
    """

    # --- Session & Target Identifiers ---
    investigation_id: str
    query: str
    top_k: int
    service_name: Optional[str]
    severity: Optional[str]
    ingestion_id: Optional[str]
    rerank: bool

    # --- Workflow Control ---
    iteration_count: int
    max_iterations: int
    investigation_status: str  # "INITIALIZED", "IN_PROGRESS", "SUCCESS", "INSUFFICIENT_EVIDENCE", "PARTIAL", "FAILED"
    errors: List[str]

    # --- Agent Findings & Deliverables ---
    retrieved_evidence: List[Dict[str, Any]]
    log_findings: Dict[str, Any]
    graph_evidence: Optional[Dict[str, Any]]
    github_evidence: Optional[Dict[str, Any]]
    blast_radius: Optional[Dict[str, Any]]
    root_cause_hypotheses: List[Dict[str, Any]]
    evidence_validation: Dict[str, Any]
    recommended_actions: List[Dict[str, Any]]

    # --- Observability & Final Synthesis ---
    agent_execution_trace: List[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]

