"""
Pydantic schemas for Gemini LLM incident analysis and evidence-grounded investigations.
Enforces strict typing, structured output contracts, and trace validation.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class InvestigationRequest(BaseModel):
    """Request payload for initiating an incident investigation."""

    query: str = Field(
        ...,
        min_length=1,
        description="Natural language incident query or symptom description",
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of evidence chunks to retrieve and analyze",
    )
    service_name: Optional[str] = Field(
        default=None,
        description="Filter retrieval to a specific microservice name",
    )
    service: Optional[str] = Field(
        default=None,
        description="Alternative alias for service_name",
    )
    severity: Optional[str] = Field(
        default=None,
        description="Filter retrieval to a specific log severity (e.g. 'ERROR', 'WARN')",
    )
    ingestion_id: Optional[str] = Field(
        default=None,
        description="Filter retrieval to a specific ingestion job",
    )
    rerank: bool = Field(
        default=True,
        description="Whether to execute Cross-Encoder reranking on retrieved candidates",
    )

    @model_validator(mode="before")
    @classmethod
    def resolve_service_alias(cls, values: Any) -> Any:
        """Allow callers to pass either 'service' or 'service_name'."""
        if isinstance(values, dict):
            if "service_name" not in values and "service" in values:
                values["service_name"] = values["service"]
        return values

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Why is the payment service failing with connection timeouts?",
                "top_k": 10,
                "service_name": "payment-service",
                "severity": "ERROR",
                "rerank": True,
            }
        }
    )


class KeyObservation(BaseModel):
    """An individual observation identified from log evidence."""

    observation: str = Field(..., description="Description of the observation")
    category: str = Field(
        default="ERROR",
        description="Category: 'ERROR', 'EXCEPTION', 'LATENCY', 'RESOURCE', 'LIFECYCLE', or 'INFO'",
    )
    is_fact: bool = Field(
        default=True,
        description="True if directly observed in log evidence; False if inferred or hypothesized",
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="Timestamp associated with this observation if present in logs",
    )
    affected_service: Optional[str] = Field(
        default=None,
        description="Microservice associated with this observation",
    )
    evidence_chunk_ids: List[str] = Field(
        default_factory=list,
        description="Chunk IDs supporting this observation",
    )


class PotentialRootCause(BaseModel):
    """A ranked hypothesis explaining the potential cause of the incident."""

    rank: int = Field(..., ge=1, description="Rank order (1 = most probable cause)")
    hypothesis: str = Field(..., description="Hypothesized root cause statement")
    reasoning: str = Field(
        ...,
        description="Explanation of why this cause is suspected based on retrieved evidence",
    )
    confidence: str = Field(
        ...,
        description="Confidence level: 'HIGH', 'MEDIUM', or 'LOW'",
    )
    confidence_reasoning: str = Field(
        ...,
        description="Justification for the confidence level assessment",
    )
    supporting_evidence_ids: List[str] = Field(
        default_factory=list,
        description="Chunk IDs directly supporting this root cause hypothesis",
    )


class SupportingEvidenceItem(BaseModel):
    """A referenced log chunk with traceability to source lines and file."""

    chunk_id: str = Field(..., description="Unique chunk identifier from hybrid retrieval")
    source_filename: str = Field(default="", description="Originating log file name")
    source_line_start: Optional[int] = Field(
        default=None,
        description="Starting line number in source log file",
    )
    source_line_end: Optional[int] = Field(
        default=None,
        description="Ending line number in source log file",
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="Timestamp or timestamp range from evidence chunk",
    )
    service_name: Optional[str] = Field(
        default=None,
        description="Service name originating the log chunk",
    )
    severity: Optional[str] = Field(
        default=None,
        description="Severity level in chunk (e.g. 'ERROR', 'CRITICAL')",
    )
    relevant_excerpt: str = Field(
        ...,
        description="Exact excerpt or verbatim line from the retrieved log content",
    )
    relevance_explanation: str = Field(
        ...,
        description="Explanation of why this specific log chunk is relevant to the incident",
    )


class RecommendedAction(BaseModel):
    """A prioritized remediation or debugging step."""

    priority: int = Field(
        ...,
        ge=1,
        description="Execution priority (1 = immediate triage/mitigation, 2 = short term fix, 3 = long term hardening)",
    )
    action: str = Field(..., description="Actionable recommendation title")
    category: str = Field(
        default="MITIGATION",
        description="Type: 'IMMEDIATE_MITIGATION', 'INVESTIGATION', 'CODE_FIX', 'CONFIGURATION', or 'MONITORING'",
    )
    rationale: str = Field(..., description="Why this action is recommended and what it resolves")


class FurtherInvestigation(BaseModel):
    """Identifies evidence gaps and recommended diagnostic steps."""

    missing_evidence: List[str] = Field(
        default_factory=list,
        description="Key logs, telemetry, or data points that were missing from available evidence",
    )
    recommended_checks: List[str] = Field(
        default_factory=list,
        description="Actionable diagnostic steps, metrics to check, or logs to gather next",
    )


class EvidenceSufficiency(BaseModel):
    """Assessment of whether retrieved logs were sufficient to diagnose the incident."""

    status: str = Field(
        ...,
        description="Assessment: 'SUFFICIENT', 'PARTIAL', or 'INSUFFICIENT'",
    )
    reason: str = Field(
        ...,
        description="Detailed explanation of the sufficiency assessment",
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Quantitative score from 0.0 (no evidence) to 1.0 (definitive evidence)",
    )


class ModelInformation(BaseModel):
    """Metadata regarding the LLM used for analysis."""

    model_name: str = Field(..., description="Name of the Gemini model used (e.g. 'gemini-flash-latest')")
    provider: str = Field(default="Google Gemini", description="Model vendor / platform")
    prompt_tokens: Optional[int] = Field(default=None, description="Number of tokens in the prompt")
    completion_tokens: Optional[int] = Field(default=None, description="Number of tokens in the completion")
    total_tokens: Optional[int] = Field(default=None, description="Total tokens consumed")
    latency_ms: Optional[float] = Field(default=None, description="Total analysis latency in milliseconds")


class InvestigationResponse(BaseModel):
    """Comprehensive evidence-grounded incident investigation report."""

    investigation_id: str = Field(..., description="Unique investigation run identifier")
    query: str = Field(..., description="Original incident inquiry")
    incident_summary: str = Field(..., description="High-level narrative explaining the incident")
    affected_services: List[str] = Field(
        default_factory=list,
        description="Microservices identified as affected by or involved in the incident",
    )
    severity_assessment: str = Field(
        ...,
        description="Estimated incident severity: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', or 'UNKNOWN'",
    )
    key_observations: List[KeyObservation] = Field(
        default_factory=list,
        description="Observable facts, exceptions, and anomalies extracted from evidence",
    )
    potential_root_causes: List[PotentialRootCause] = Field(
        default_factory=list,
        description="Ranked root cause hypotheses supported by evidence references",
    )
    supporting_evidence: List[SupportingEvidenceItem] = Field(
        default_factory=list,
        description="Detailed log evidence references with source line numbers and excerpts",
    )
    recommended_actions: List[RecommendedAction] = Field(
        default_factory=list,
        description="Prioritized remediation and debugging recommendations",
    )
    further_investigation: FurtherInvestigation = Field(
        default_factory=FurtherInvestigation,
        description="Missing evidence items and next-step diagnostic checks",
    )
    evidence_sufficiency: EvidenceSufficiency = Field(
        ...,
        description="Evaluation of whether retrieved logs provided enough evidence for root cause analysis",
    )
    model_information: ModelInformation = Field(
        ...,
        description="Metadata on the Gemini model and inference diagnostics",
    )
    retrieved_chunks_count: int = Field(
        default=0,
        description="Total number of evidence chunks retrieved by hybrid search",
    )
    created_at: str = Field(..., description="ISO 8601 timestamp of investigation completion")


class AgentExecutionStep(BaseModel):
    """Audit log entry capturing individual agent execution in the LangGraph workflow."""

    agent_name: str = Field(..., description="Name of the executing agent")
    stage: str = Field(..., description="Workflow phase or node identifier")
    status: str = Field(default="COMPLETED", description="Status: 'COMPLETED', 'SKIPPED', or 'FAILED'")
    timestamp: str = Field(..., description="ISO 8601 timestamp of agent step completion")
    summary: str = Field(..., description="Summary of work performed or decisions taken")
    latency_ms: Optional[float] = Field(default=None, description="Execution time in milliseconds")


class AgenticInvestigationResponse(InvestigationResponse):
    """Investigation report enriched with LangGraph multi-agent orchestration metadata."""

    workflow_status: str = Field(
        default="SUCCESS",
        description="Overall workflow status: 'SUCCESS', 'INSUFFICIENT_EVIDENCE', 'PARTIAL', or 'FAILED'",
    )
    iterations_executed: int = Field(
        default=1,
        description="Number of retrieval and analysis iterations executed by the multi-agent graph",
    )
    agent_execution_trace: List[AgentExecutionStep] = Field(
        default_factory=list,
        description="Ordered trace of agent decisions and execution steps",
    )
    graph_evidence: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Knowledge graph evidence including service topology, dependencies, and blast radius",
    )
    github_evidence: Optional[Dict[str, Any]] = Field(
        default=None,
        description="GitHub commit and diff correlation evidence",
    )
    blast_radius: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Assessed blast radius and cascade failure potential",
    )

