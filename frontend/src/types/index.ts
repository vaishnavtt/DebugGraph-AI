/**
 * Unified TypeScript types for DebugGraph AI frontend.
 * Strictly aligned with FastAPI backend Pydantic models.
 */

// ============================================================================
// 1. System Health & Overview
// ============================================================================
export interface SystemOverview {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  ai_model: string;
  services: {
    database: string;
    neo4j: string;
    qdrant: string;
  };
  metrics: {
    total_ingested_logs: number;
    total_indexed_chunks: number;
    total_graph_services: number;
    github_integration_enabled: boolean;
  };
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
}

// ============================================================================
// 2. Incident Investigation & LangGraph Multi-Agent
// ============================================================================
export interface KeyObservation {
  observation: string;
  category: string;
  is_fact: boolean;
  timestamp?: string | null;
  affected_service?: string | null;
  evidence_chunk_ids: string[];
}

export interface PotentialRootCause {
  rank: number;
  hypothesis: string;
  reasoning: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  confidence_reasoning?: string | null;
  supporting_evidence_ids: string[];
}

export interface SupportingEvidenceItem {
  chunk_id: string;
  source_filename?: string | null;
  source_line_start?: number | null;
  source_line_end?: number | null;
  timestamp?: string | null;
  service_name?: string | null;
  severity?: string | null;
  relevant_excerpt: string;
  relevance_explanation?: string | null;
}

export interface RecommendedAction {
  priority: number | string;
  action: string;
  category: string;
  rationale: string;
  safety_warning?: string | null;
  title?: string;
  action_type?: string;
  description?: string;
  command_snippet?: string;
}

export interface EvidenceSufficiency {
  status: 'SUFFICIENT' | 'PARTIAL' | 'INSUFFICIENT';
  reason: string;
  confidence_score: number;
}

export interface AgentExecutionStep {
  agent_name: string;
  stage: string;
  status: 'COMPLETED' | 'SKIPPED' | 'FAILED';
  timestamp: string;
  summary: string;
  latency_ms?: number | null;
}

export interface InvestigationResponse {
  investigation_id: string;
  query: string;
  incident_summary: string;
  affected_services: string[];
  severity_assessment: string;
  key_observations: KeyObservation[];
  potential_root_causes: PotentialRootCause[];
  supporting_evidence: SupportingEvidenceItem[];
  recommended_actions: RecommendedAction[];
  further_investigation: {
    missing_evidence: string[];
    recommended_checks: string[];
  };
  evidence_sufficiency: EvidenceSufficiency;
  model_information: {
    model_name: string;
    provider: string;
    latency_ms?: number | null;
  };
  retrieved_chunks_count: number;
  created_at: string;

  // Agentic-specific fields (when returned by /agentic)
  workflow_status?: string;
  iterations_executed?: number;
  agent_execution_trace?: AgentExecutionStep[];
  graph_evidence?: any;
  github_evidence?: any;
  blast_radius?: any;
}

export interface InvestigationRequest {
  query: string;
  service_name?: string;
  severity?: string;
  top_k?: number;
  rerank?: boolean;
}

// ============================================================================
// 3. Neo4j Knowledge Graph & Topology
// ============================================================================
export interface ServiceDetail {
  name: string;
  environment: string;
  tier?: string | null;
  team?: string | null;
  status: string;
  metadata: Record<string, any>;
  upstream_dependencies: string[];
  downstream_dependencies: string[];
  connected_databases: string[];
  connected_apis: string[];
  repositories: string[];
}

export interface ServiceDependencies {
  service_name: string;
  direction: string;
  max_depth: number;
  upstream: string[];
  downstream: string[];
  databases: string[];
  apis: string[];
  traversal_paths: string[][];
}

export interface BlastRadius {
  service_name: string;
  blast_radius_score: number;
  severity_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  direct_dependents_count: number;
  total_impacted_services_count: number;
  impacted_services: string[];
  impacted_databases: string[];
  impacted_apis: string[];
  dependency_chains: string[][];
}

export interface GraphHealth {
  status: string;
  connected: boolean;
  uri: string;
  database: string;
  node_counts?: Record<string, number> | null;
  error?: string | null;
}

// ============================================================================
// 4. GitHub Intelligence
// ============================================================================
export interface RepositoryItem {
  owner: string;
  repo: string;
  url: string;
  service_name?: string | null;
  default_branch: string;
  description?: string | null;
  language?: string | null;
  stars: number;
  forks: number;
  is_private: boolean;
  registered_at: string;
}

export interface CommitSummary {
  sha: string;
  short_sha: string;
  message: string;
  author: string;
  date: string;
  url: string;
  files_changed_count?: number | null;
}

export interface CommitFileDiff {
  filename: string;
  status: string;
  additions: number;
  deletions: number;
  changes: number;
  patch?: string | null;
}

export interface CommitDetails {
  sha: string;
  short_sha: string;
  message: string;
  author: string;
  date: string;
  url: string;
  stats: Record<string, number>;
  files: CommitFileDiff[];
}

// ============================================================================
// 5. Evaluation & Benchmarking
// ============================================================================
export interface RetrievalMetrics {
  recall_at_1: number;
  recall_at_3: number;
  recall_at_5: number;
  precision_at_5: number;
  mrr: number;
  ndcg_at_5: number;
  average_latency_ms: number;
}

export interface RetrievalMethodComparison {
  method: string;
  metrics: RetrievalMetrics;
  queries_evaluated: number;
}

export interface InvestigationMetrics {
  citation_precision: number;
  citation_recall: number;
  evidence_groundedness: number;
  category_accuracy: number;
  recommendation_relevance: number;
  average_latency_ms: number;
}

export interface InvestigationModeComparison {
  mode: string;
  metrics: InvestigationMetrics;
  average_chunks_retrieved: number;
  average_iterations: number;
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  } | null;
}

export interface EvaluationRunReport {
  run_id: string;
  timestamp: string;
  dataset_name: string;
  dataset_size: number;
  retrieval_comparisons: RetrievalMethodComparison[];
  investigation_comparisons: InvestigationModeComparison[];
  summary_markdown: string;
  execution_time_seconds: number;
}

export interface DatasetInfo {
  dataset_name: string;
  total_retrieval_queries: number;
  retrieval_categories: string[];
  sample_queries: Array<{
    query_id: string;
    category: string;
    query: string;
  }>;
  total_incident_scenarios: number;
  incident_categories: string[];
  description: string;
}

