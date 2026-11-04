import {
  BlastRadius,
  CommitDetails,
  CommitSummary,
  DatasetInfo,
  EvaluationRunReport,
  GraphHealth,
  HealthResponse,
  InvestigationRequest,
  InvestigationResponse,
  RepositoryItem,
  ServiceDependencies,
  ServiceDetail,
  SystemOverview,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
        try {
          const errData = await response.json();
          errorMsg = errData.detail || errData.message || errorMsg;
        } catch {
          // fallback to status text
        }
        throw new Error(errorMsg);
      }

      return (await response.json()) as T;
    } catch (err: any) {
      console.error(`API Error on [${options.method || 'GET'}] ${url}:`, err);
      throw err;
    }
  }

  // ==========================================================================
  // 1. Overview & System Telemetry
  // ==========================================================================
  async getOverview(): Promise<SystemOverview> {
    return this.request<SystemOverview>('/health/overview');
  }

  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  // ==========================================================================
  // 2. Incident Investigations
  // ==========================================================================
  async runStandardInvestigation(req: InvestigationRequest): Promise<InvestigationResponse> {
    return this.request<InvestigationResponse>('/analysis/investigate', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  async runAgenticInvestigation(req: InvestigationRequest): Promise<InvestigationResponse> {
    return this.request<InvestigationResponse>('/analysis/investigate/agentic', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  // ==========================================================================
  // 3. Log Ingestion & Indexing
  // ==========================================================================
  async uploadLogs(file: File, serviceName?: string, environment?: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (serviceName) formData.append('service_name', serviceName);
    if (environment) formData.append('environment', environment);

    const response = await fetch(`${BASE_URL}/logs/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to upload log file');
    }

    return response.json();
  }

  async getIndexingStatus(): Promise<any> {
    return this.request<any>('/indexing/status');
  }

  async searchHybrid(query: string, serviceName?: string, topK: number = 10): Promise<any> {
    return this.request<any>('/search/hybrid', {
      method: 'POST',
      body: JSON.stringify({
        query,
        service_name: serviceName,
        top_k: topK,
      }),
    });
  }

  // ==========================================================================
  // 4. Neo4j Knowledge Graph & Topology
  // ==========================================================================
  async getGraphHealth(): Promise<GraphHealth> {
    return this.request<GraphHealth>('/graph/health');
  }

  async getService(name: string): Promise<ServiceDetail> {
    return this.request<ServiceDetail>(`/graph/services/${encodeURIComponent(name)}`);
  }

  async getServiceDependencies(
    name: string,
    direction: 'both' | 'upstream' | 'downstream' = 'both',
    maxDepth: number = 2
  ): Promise<ServiceDependencies> {
    return this.request<ServiceDependencies>(
      `/graph/services/${encodeURIComponent(name)}/dependencies?direction=${direction}&max_depth=${maxDepth}`
    );
  }

  async getBlastRadius(name: string, maxDepth: number = 3): Promise<BlastRadius> {
    return this.request<BlastRadius>(
      `/graph/services/${encodeURIComponent(name)}/blast-radius?max_depth=${maxDepth}`
    );
  }

  async registerService(payload: {
    name: string;
    environment?: string;
    tier?: string;
    team?: string;
  }): Promise<any> {
    return this.request<any>('/graph/services', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async registerDependency(payload: {
    source: string;
    target: string;
    relation_type?: string;
  }): Promise<any> {
    return this.request<any>('/graph/dependencies', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // ==========================================================================
  // 5. GitHub Intelligence
  // ==========================================================================
  async registerRepository(payload: {
    url: string;
    service_name?: string;
    default_branch?: string;
  }): Promise<RepositoryItem> {
    return this.request<RepositoryItem>('/github/repositories', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getRepository(owner: string, repo: string): Promise<RepositoryItem> {
    return this.request<RepositoryItem>(`/github/repositories/${owner}/${repo}`);
  }

  async getRepositoryCommits(owner: string, repo: string, limit: number = 10): Promise<CommitSummary[]> {
    return this.request<CommitSummary[]>(`/github/repositories/${owner}/${repo}/commits?limit=${limit}`);
  }

  async getCommitDetails(owner: string, repo: string, sha: string): Promise<CommitDetails> {
    return this.request<CommitDetails>(`/github/repositories/${owner}/${repo}/commits/${sha}`);
  }

  // ==========================================================================
  // 6. Evaluation & Benchmarking
  // ==========================================================================
  async getLatestEvaluation(): Promise<EvaluationRunReport> {
    return this.request<EvaluationRunReport>('/evaluation/latest');
  }

  async triggerEvaluation(payload: {
    evaluate_retrieval?: boolean;
    evaluate_investigation?: boolean;
    max_queries?: number;
  }): Promise<EvaluationRunReport> {
    return this.request<EvaluationRunReport>('/evaluation/run', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getEvaluationDataset(): Promise<DatasetInfo> {
    return this.request<DatasetInfo>('/evaluation/dataset');
  }

  getMarkdownReportUrl(runId: string = 'latest'): string {
    return `${BASE_URL}/evaluation/reports/${runId}/markdown`;
  }
}

export const api = new ApiClient();

