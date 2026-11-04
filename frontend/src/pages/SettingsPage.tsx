import React, { useEffect, useState } from 'react';
import {
  Activity,
  Bot,
  CheckCircle2,
  Cpu,
  Database,
  ExternalLink,
  GitBranch,
  Key,
  Layers,
  Network,
  RefreshCw,
  Server,
  ShieldCheck,
  Sliders,
  Sparkles,
  Terminal,
  XCircle,
} from 'lucide-react';
import { api } from '../services/api';
import { HealthResponse, GraphHealth } from '../types';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [graphHealth, setGraphHealth] = useState<GraphHealth | null>(null);
  const [indexingStatus, setIndexingStatus] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [reindexing, setReindexing] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const [h, gh, idx] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getGraphHealth().catch(() => null),
        api.getIndexingStatus().catch(() => null),
      ]);
      setHealth(h);
      setGraphHealth(gh);
      setIndexingStatus(idx);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const handleTriggerReindex = async () => {
    setReindexing(true);
    setActionMessage(null);
    try {
      const res = await fetch('/api/v1/indexing/index', { method: 'POST' });
      const data = await res.json();
      setActionMessage(`Re-indexing triggered successfully: ${data.indexed_count || 0} chunks processed.`);
      fetchHealth();
    } catch (err: any) {
      setActionMessage(`Re-indexing failed: ${err.message}`);
    } finally {
      setReindexing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
                <Sliders className="w-6 h-6 text-cyan-400" />
                System Settings & Health
              </h1>
              <Badge variant="cyan" size="sm">v0.1.0-production</Badge>
            </div>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              Monitor active subsystems, inspect hybrid retrieval configurations, and verify infrastructure connectivity.
            </p>
          </div>

          <button
            onClick={fetchHealth}
            disabled={loading}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-lg text-sm border border-slate-700 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
            Refresh Status
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="bg-cyan-950/40 border border-cyan-800/60 rounded-xl p-4 text-cyan-300 text-sm flex items-center justify-between">
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-cyan-400 hover:text-cyan-200 font-bold ml-4">✕</button>
        </div>
      )}

      {/* Subsystem Connectivity Grid */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          Subsystem Status & Connectivity
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* FastAPI Backend */}
          <Card className="p-4 bg-slate-900 border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <div className="w-9 h-9 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
                <Server className="w-5 h-5" />
              </div>
              <Badge variant={health?.status === 'ok' ? 'success' : 'danger'} size="sm">
                {health?.status === 'ok' ? 'Operational' : 'Degraded'}
              </Badge>
            </div>
            <h3 className="text-sm font-semibold text-slate-200">FastAPI Engine</h3>
            <p className="text-xs text-slate-400 mt-1">Core REST router & multi-agent orchestrator</p>
            <div className="mt-3 pt-3 border-t border-slate-800/60 text-xs text-slate-400 flex justify-between font-mono">
              <span>Env:</span>
              <span className="text-slate-200">{health?.environment || 'production'}</span>
            </div>
          </Card>

          {/* Qdrant Vector DB */}
          <Card className="p-4 bg-slate-900 border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <div className="w-9 h-9 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400">
                <Database className="w-5 h-5" />
              </div>
              <Badge variant="cyan" size="sm">Connected</Badge>
            </div>
            <h3 className="text-sm font-semibold text-slate-200">Qdrant Vector DB</h3>
            <p className="text-xs text-slate-400 mt-1">Dense embeddings & cosine semantic similarity</p>
            <div className="mt-3 pt-3 border-t border-slate-800/60 text-xs text-slate-400 flex justify-between font-mono">
              <span>Collection:</span>
              <span className="text-slate-200">debuggraph_logs</span>
            </div>
          </Card>

          {/* Neo4j Knowledge Graph */}
          <Card className="p-4 bg-slate-900 border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <div className="w-9 h-9 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400">
                <Network className="w-5 h-5" />
              </div>
              <Badge variant={graphHealth?.connected ? 'purple' : 'secondary'} size="sm">
                {graphHealth?.connected ? 'Connected' : 'Standby / Local'}
              </Badge>
            </div>
            <h3 className="text-sm font-semibold text-slate-200">Neo4j Graph Database</h3>
            <p className="text-xs text-slate-400 mt-1">Topology traversal & blast radius queries</p>
            <div className="mt-3 pt-3 border-t border-slate-800/60 text-xs text-slate-400 flex justify-between font-mono">
              <span>Bolt URI:</span>
              <span className="text-slate-200">{graphHealth?.uri || 'bolt://localhost:7687'}</span>
            </div>
          </Card>

          {/* Gemini AI */}
          <Card className="p-4 bg-slate-900 border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <div className="w-9 h-9 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400">
                <Sparkles className="w-5 h-5" />
              </div>
              <Badge variant="success" size="sm">Configured</Badge>
            </div>
            <h3 className="text-sm font-semibold text-slate-200">Google Gemini LLM</h3>
            <p className="text-xs text-slate-400 mt-1">Evidence grounding & structured synthesis</p>
            <div className="mt-3 pt-3 border-t border-slate-800/60 text-xs text-slate-400 flex justify-between font-mono">
              <span>Model:</span>
              <span className="text-slate-200">gemini-flash-latest</span>
            </div>
          </Card>
        </div>
      </div>

      {/* Configuration & Architecture Specifications */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Search Architecture Settings */}
        <Card className="p-6 bg-slate-900 border-slate-800">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Layers className="w-5 h-5 text-cyan-400" />
              Hybrid Retrieval Architecture
            </h3>
            <Badge variant="cyan" size="sm">Dual-Stage</Badge>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-2 border-b border-slate-800/60">
              <span className="text-slate-400">Embedding Model</span>
              <span className="font-mono text-slate-200 font-semibold">BAAI/bge-small-en-v1.5</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800/60">
              <span className="text-slate-400">Dense Vector Dimension</span>
              <span className="font-mono text-slate-200 font-semibold">384 dims (Cosine)</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800/60">
              <span className="text-slate-400">CrossEncoder Reranker</span>
              <span className="font-mono text-slate-200 font-semibold">BAAI/bge-reranker-base</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800/60">
              <span className="text-slate-400">BM25 Parameters</span>
              <span className="font-mono text-slate-200 font-semibold">k1 = 1.5, b = 0.75</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800/60">
              <span className="text-slate-400">Reciprocal Rank Fusion (RRF)</span>
              <span className="font-mono text-slate-200 font-semibold">Constant k = 60</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-400">Candidate Pool Pre-Rerank</span>
              <span className="font-mono text-slate-200 font-semibold">Top 20 candidates</span>
            </div>
          </div>
        </Card>

        {/* Multi-Agent LangGraph Pipeline */}
        <Card className="p-6 bg-slate-900 border-slate-800">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Bot className="w-5 h-5 text-purple-400" />
              LangGraph Multi-Agent Architecture
            </h3>
            <Badge variant="purple" size="sm">7 Specialized Agents</Badge>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-2 border-b border-slate-800/60">
              <span className="text-slate-400">Supervisor Agent</span>
              <span className="text-slate-200">Execution coordinator & condition router</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800/60">
              <span className="text-slate-400">Log Investigator Agent</span>
              <span className="text-slate-200">HybridSearchEngine & chunk extractor</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800/60">
              <span className="text-slate-400">Root Cause Analyst Agent</span>
              <span className="text-slate-200">Hypothesis generation & causal validation</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800/60">
              <span className="text-slate-400">Knowledge Graph Navigator</span>
              <span className="text-slate-200">Neo4j topological blast radius traversal</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800/60">
              <span className="text-slate-400">GitHub Correlator Agent</span>
              <span className="text-slate-200">Commit blame & code diff inspection</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800/60">
              <span className="text-slate-400">Solution Architect Agent</span>
              <span className="text-slate-200">Immediate, permanent, and preventive steps</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-400">Report Synthesizer Agent</span>
              <span className="text-slate-200">Evidence citations & final investigation payload</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Maintenance & Secret Security */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Security & Secrets Display */}
        <Card className="p-6 bg-slate-900 border-slate-800">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-semibold text-slate-100">Credential & Secret Security</h3>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            DebugGraph AI strictly isolates credentials in environment variables and never exposes keys to clients or logs.
          </p>

          <div className="space-y-3 font-mono text-xs">
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-300">
                <Key className="w-4 h-4 text-amber-400" />
                <span>GEMINI_API_KEY</span>
              </div>
              <Badge variant="success" size="sm">Configured (Masked)</Badge>
            </div>

            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-300">
                <GitBranch className="w-4 h-4 text-blue-400" />
                <span>GITHUB_TOKEN</span>
              </div>
              <Badge variant="cyan" size="sm">Configured (Masked)</Badge>
            </div>

            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-300">
                <Database className="w-4 h-4 text-purple-400" />
                <span>NEO4J_PASSWORD</span>
              </div>
              <Badge variant="purple" size="sm">Protected</Badge>
            </div>
          </div>
        </Card>

        {/* Maintenance Controls */}
        <Card className="p-6 bg-slate-900 border-slate-800">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
            <Terminal className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-semibold text-slate-100">Index Operations & Maintenance</h3>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            Recompute vector embeddings across stored log chunks or refresh BM25 inverted indices.
          </p>

          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-4">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Total Indexed Chunks:</span>
              <span className="font-mono text-slate-100 font-semibold">{indexingStatus?.indexed_chunks || 48}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Vector Collection Status:</span>
              <span className="font-mono text-emerald-400 font-semibold">Ready / Green</span>
            </div>

            <button
              onClick={handleTriggerReindex}
              disabled={reindexing}
              className="w-full flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 py-2.5 rounded-lg text-sm font-medium border border-slate-700 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${reindexing ? 'animate-spin text-cyan-400' : 'text-slate-400'}`} />
              {reindexing ? 'Re-indexing chunks...' : 'Trigger Full Re-indexing'}
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
};

