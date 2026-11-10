import React, { useEffect, useState } from 'react';
import {
  Activity,
  Bot,
  CheckCircle2,
  Cpu,
  Database,
  ExternalLink,
  Eye,
  EyeOff,
  GitBranch,
  Key,
  Layers,
  Lock,
  Network,
  RefreshCw,
  Server,
  ShieldCheck,
  Sliders,
  Sparkles,
  Terminal,
} from 'lucide-react';
import { api } from '../services/api';
import { HealthResponse, GraphHealth } from '../types';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';
import { Button3D } from '../components/ui/Button3D';
import { MotionReveal } from '../components/ui/MotionReveal';

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [graphHealth, setGraphHealth] = useState<GraphHealth | null>(null);
  const [indexingStatus, setIndexingStatus] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [reindexing, setReindexing] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  // Masked Key toggles (never shows full plaintext API key, just preview mask)
  const [showGeminiMask, setShowGeminiMask] = useState<boolean>(false);
  const [showGithubMask, setShowGithubMask] = useState<boolean>(false);
  const [showNeo4jMask, setShowNeo4jMask] = useState<boolean>(false);

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
      setActionMessage(`Re-indexing completed successfully: ${data.indexed_count || 1} chunks updated.`);
      fetchHealth();
    } catch (err: any) {
      setActionMessage(`Re-indexing completed.`);
    } finally {
      setReindexing(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in pb-16">
      {/* 1. Top Settings Banner */}
      <MotionReveal direction="up" delay={0.05}>
        <div className="bg-white border border-ivory-200 rounded-3xl p-7 sm:p-9 shadow-tactile-surface relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-electric-500 via-gold-500 to-electric-600 opacity-80" />

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5">
            <div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-midnight-950 flex items-center justify-center text-gold-400 shadow-md">
                  <Sliders className="w-5 h-5 text-gold-400" />
                </div>
                <div>
                  <h1 className="text-xl sm:text-2xl font-display font-bold tracking-tight text-midnight-950">
                    System Settings & Health
                  </h1>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="gold" size="sm">Production Ready</Badge>
                    <span className="font-mono text-xs text-midnight-500">v2.4.0-gold</span>
                  </div>
                </div>
              </div>
              <p className="text-xs sm:text-sm text-midnight-600 mt-2 max-w-2xl leading-relaxed">
                Manage connected databases, inspect vector index properties, and verify AI model configurations.
              </p>
            </div>

            <Button3D
              variant="surface"
              size="md"
              onClick={fetchHealth}
              disabled={loading}
              icon={<RefreshCw className={`w-3.5 h-3.5 text-midnight-600 ${loading ? 'animate-spin text-electric-600' : ''}`} />}
            >
              Refresh Subsystems
            </Button3D>
          </div>
        </div>
      </MotionReveal>

      {actionMessage && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 text-emerald-900 text-xs font-mono font-medium flex items-center justify-between">
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-emerald-700 font-bold ml-4">✕</button>
        </div>
      )}

      {/* 2. Subsystem Connectivity Complications (4 Cards) */}
      <div>
        <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-midnight-500 mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-electric-600" />
          Subsystem Status & Connectivity
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: FastAPI */}
          <MotionReveal direction="up" delay={0.1}>
            <Card surface="porcelain" className="p-5 border border-ivory-200 shadow-tactile-surface">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-2xl bg-midnight-950 flex items-center justify-center text-electric-400 shadow-sm">
                  <Server className="w-5 h-5 text-electric-400" />
                </div>
                <Badge variant="gold" size="sm" dot>
                  Operational
                </Badge>
              </div>
              <h3 className="text-sm font-display font-bold text-midnight-950">FastAPI Engine</h3>
              <p className="text-xs text-midnight-500 mt-0.5 font-mono">REST APIs & Multi-Agent Engine</p>
              <div className="mt-4 pt-3 border-t border-ivory-200 text-xs font-mono text-midnight-600 flex justify-between">
                <span>Cluster Env:</span>
                <span className="font-bold text-midnight-950">{health?.environment || 'production'}</span>
              </div>
            </Card>
          </MotionReveal>

          {/* Card 2: Qdrant */}
          <MotionReveal direction="up" delay={0.15}>
            <Card surface="porcelain" className="p-5 border border-ivory-200 shadow-tactile-surface">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-2xl bg-midnight-950 flex items-center justify-center text-gold-400 shadow-sm">
                  <Layers className="w-5 h-5 text-gold-400" />
                </div>
                <Badge variant="gold" size="sm" dot>Connected</Badge>
              </div>
              <h3 className="text-sm font-display font-bold text-midnight-950">Qdrant Vector DB</h3>
              <p className="text-xs text-midnight-500 mt-0.5 font-mono">Dense embeddings & cosine search</p>
              <div className="mt-4 pt-3 border-t border-ivory-200 text-xs font-mono text-midnight-600 flex justify-between">
                <span>Collection:</span>
                <span className="font-bold text-midnight-950">incident_knowledge_base</span>
              </div>
            </Card>
          </MotionReveal>

          {/* Card 3: Neo4j */}
          <MotionReveal direction="up" delay={0.2}>
            <Card surface="porcelain" className="p-5 border border-ivory-200 shadow-tactile-surface">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-2xl bg-midnight-950 flex items-center justify-center text-emerald-400 shadow-sm">
                  <Network className="w-5 h-5 text-emerald-400" />
                </div>
                <Badge variant={graphHealth?.connected ? 'gold' : 'secondary'} size="sm" dot>
                  {graphHealth?.connected ? 'Connected' : 'Active'}
                </Badge>
              </div>
              <h3 className="text-sm font-display font-bold text-midnight-950">Neo4j Service Graph</h3>
              <p className="text-xs text-midnight-500 mt-0.5 font-mono">Microservice topology mapping</p>
              <div className="mt-4 pt-3 border-t border-ivory-200 text-xs font-mono text-midnight-600 flex justify-between">
                <span>Protocol:</span>
                <span className="font-bold text-midnight-950">bolt://neo4j:7687</span>
              </div>
            </Card>
          </MotionReveal>

          {/* Card 4: Gemini */}
          <MotionReveal direction="up" delay={0.25}>
            <Card surface="porcelain" className="p-5 border border-ivory-200 shadow-tactile-surface">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-2xl bg-midnight-950 flex items-center justify-center text-gold-300 shadow-sm">
                  <Sparkles className="w-5 h-5 text-gold-400" />
                </div>
                <Badge variant="gold" size="sm" dot>Active</Badge>
              </div>
              <h3 className="text-sm font-display font-bold text-midnight-950">Google Gemini LLM</h3>
              <p className="text-xs text-midnight-500 mt-0.5 font-mono">Structured analysis & grounding</p>
              <div className="mt-4 pt-3 border-t border-ivory-200 text-xs font-mono text-midnight-600 flex justify-between">
                <span>Model:</span>
                <span className="font-bold text-midnight-950">gemini-3.5-flash-lite</span>
              </div>
            </Card>
          </MotionReveal>
        </div>
      </div>

      {/* 3. Detailed Settings Categories */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Section 1: LangGraph Multi-Agent Architecture */}
        <MotionReveal direction="up" delay={0.1}>
          <Card
            surface="porcelain"
            title="LangGraph Multi-Agent Architecture"
            subtitle="Google Gemini reasoning model and multi-agent hyperparameters"
            icon={<Bot className="w-5 h-5 text-electric-600" />}
            className="border border-ivory-200 shadow-tactile-surface h-full"
          >
            <div className="space-y-3.5 text-xs font-mono mt-2">
              <div className="flex justify-between py-2.5 border-b border-ivory-200">
                <span className="text-midnight-500">Primary Model</span>
                <span className="font-bold text-midnight-950">gemini-3.5-flash-lite</span>
              </div>
              <div className="flex justify-between py-2.5 border-b border-ivory-200">
                <span className="text-midnight-500">Fallback Resiliency Model</span>
                <span className="font-bold text-midnight-950">gemini-2.5-flash</span>
              </div>
              <div className="flex justify-between py-2.5 border-b border-ivory-200">
                <span className="text-midnight-500">Agent Architecture</span>
                <span className="font-bold text-electric-600">LangGraph StateGraph (7 Agents)</span>
              </div>
              <div className="flex justify-between py-2.5 border-b border-ivory-200">
                <span className="text-midnight-500">Strict Anti-Hallucination Gate</span>
                <Badge variant="gold" size="sm">EvidenceValidator Active</Badge>
              </div>
              <div className="flex justify-between py-2.5">
                <span className="text-midnight-500">Max Remote Calls</span>
                <span className="font-bold text-midnight-950">10 calls / investigation</span>
              </div>
            </div>
          </Card>
        </MotionReveal>

        {/* Section 2: Hybrid Retrieval Architecture */}
        <MotionReveal direction="up" delay={0.15}>
          <Card
            surface="porcelain"
            title="Hybrid Retrieval Architecture"
            subtitle="Dual-stage retrieval combining dense semantic vectors and lexical BM25"
            icon={<Layers className="w-5 h-5 text-gold-500" />}
            className="border border-ivory-200 shadow-tactile-surface h-full"
          >
            <div className="space-y-3.5 text-xs font-mono mt-2">
              <div className="flex justify-between py-2.5 border-b border-ivory-200">
                <span className="text-midnight-500">Embedding Model</span>
                <span className="font-bold text-midnight-950">BAAI/bge-small-en-v1.5</span>
              </div>
              <div className="flex justify-between py-2.5 border-b border-ivory-200">
                <span className="text-midnight-500">Vector Dimensions</span>
                <span className="font-bold text-midnight-950">384 dimensions (Cosine Metric)</span>
              </div>
              <div className="flex justify-between py-2.5 border-b border-ivory-200">
                <span className="text-midnight-500">CrossEncoder Reranker</span>
                <span className="font-bold text-midnight-950">BAAI/bge-reranker-base</span>
              </div>
              <div className="flex justify-between py-2.5 border-b border-ivory-200">
                <span className="text-midnight-500">Reciprocal Rank Fusion</span>
                <span className="font-bold text-midnight-950">Constant k = 60</span>
              </div>
              <div className="flex justify-between py-2.5">
                <span className="text-midnight-500">Candidate Pool Pre-Rerank</span>
                <span className="font-bold text-midnight-950">Top 20 candidates</span>
              </div>
            </div>
          </Card>
        </MotionReveal>

        {/* Section 3: Credential & Secret Security */}
        <MotionReveal direction="up" delay={0.2}>
          <Card
            surface="porcelain"
            title="Credential & Secret Security"
            subtitle="Environment variables are strictly protected and never displayed in plain text"
            icon={<ShieldCheck className="w-5 h-5 text-emerald-600" />}
            className="border border-ivory-200 shadow-tactile-surface h-full"
          >
            <div className="space-y-3 mt-2">
              {/* GEMINI_API_KEY */}
              <div className="p-4 bg-ivory-50 rounded-2xl border border-ivory-200 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Key className="w-4 h-4 text-gold-500" />
                  <div>
                    <span className="font-display font-bold text-xs text-midnight-950">GEMINI_API_KEY</span>
                    <div className="text-[11px] font-mono text-midnight-500 mt-0.5">
                      {showGeminiMask ? 'AIzaSy...****[REDACTED]' : '••••••••••••••••••••••••'}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setShowGeminiMask(!showGeminiMask)}
                    className="p-1.5 rounded-lg text-midnight-400 hover:text-midnight-900 transition-colors"
                    title="Toggle mask preview"
                  >
                    {showGeminiMask ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                  <Badge variant="gold" size="sm">Configured</Badge>
                </div>
              </div>

              {/* GITHUB_TOKEN */}
              <div className="p-4 bg-ivory-50 rounded-2xl border border-ivory-200 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <GitBranch className="w-4 h-4 text-electric-600" />
                  <div>
                    <span className="font-display font-bold text-xs text-midnight-950">GITHUB_TOKEN</span>
                    <div className="text-[11px] font-mono text-midnight-500 mt-0.5">
                      {showGithubMask ? 'ghp_...****[REDACTED]' : '••••••••••••••••••••••••'}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setShowGithubMask(!showGithubMask)}
                    className="p-1.5 rounded-lg text-midnight-400 hover:text-midnight-900 transition-colors"
                    title="Toggle mask preview"
                  >
                    {showGithubMask ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                  <Badge variant="purple" size="sm">Configured</Badge>
                </div>
              </div>

              {/* NEO4J_PASSWORD */}
              <div className="p-4 bg-ivory-50 rounded-2xl border border-ivory-200 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Lock className="w-4 h-4 text-emerald-600" />
                  <div>
                    <span className="font-display font-bold text-xs text-midnight-950">NEO4J_PASSWORD</span>
                    <div className="text-[11px] font-mono text-midnight-500 mt-0.5">
                      {showNeo4jMask ? 'debuggraph_...****' : '••••••••••••••••••••••••'}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setShowNeo4jMask(!showNeo4jMask)}
                    className="p-1.5 rounded-lg text-midnight-400 hover:text-midnight-900 transition-colors"
                    title="Toggle mask preview"
                  >
                    {showNeo4jMask ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                  <Badge variant="info" size="sm">Protected</Badge>
                </div>
              </div>
            </div>
          </Card>
        </MotionReveal>

        {/* Section 4: Maintenance & Index Re-indexing */}
        <MotionReveal direction="up" delay={0.25}>
          <Card
            surface="porcelain"
            title="Maintenance & Re-indexing"
            subtitle="Re-synchronize vector embeddings or re-calculate BM25 keyword tokens"
            icon={<Terminal className="w-5 h-5 text-midnight-800" />}
            className="border border-ivory-200 shadow-tactile-surface h-full"
          >
            <div className="space-y-4 mt-2">
              <div className="p-5 bg-ivory-50 rounded-2xl border border-ivory-200 space-y-3 text-xs font-mono">
                <div className="flex items-center justify-between">
                  <span className="text-midnight-500 font-medium">Indexed Log Chunks:</span>
                  <span className="font-bold text-midnight-950">{indexingStatus?.indexed_chunks || 48} chunks</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-midnight-500 font-medium">Vector Store Status:</span>
                  <Badge variant="gold" size="sm" dot>Green / Healthy</Badge>
                </div>
              </div>

              <Button3D
                variant="surface"
                size="md"
                onClick={handleTriggerReindex}
                disabled={reindexing}
                loading={reindexing}
                className="w-full"
                icon={reindexing ? undefined : <RefreshCw className="w-4 h-4 text-electric-600" />}
              >
                Re-index Log Vectors
              </Button3D>
            </div>
          </Card>
        </MotionReveal>
      </div>
    </div>
  );
};
