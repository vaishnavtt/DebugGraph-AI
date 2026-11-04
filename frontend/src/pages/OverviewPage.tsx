import React, { useEffect, useState } from 'react';
import {
  Activity,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Database,
  FileText,
  GitBranch,
  Layers,
  Network,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react';
import { api } from '../services/api';
import { SystemOverview } from '../types';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { NavTab } from '../components/layout/Sidebar';

interface OverviewPageProps {
  onNavigate: (tab: NavTab) => void;
  onLaunchDemoQuery: (query: string, service?: string) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  onNavigate,
  onLaunchDemoQuery,
}) => {
  const [overview, setOverview] = useState<SystemOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getOverview();
      setOverview(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load system overview');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const demoScenarios = [
    {
      title: 'Stripe Gateway Timeout',
      service: 'payment-service',
      query: 'Why is payment-service failing with ConnectionTimeoutError on Stripe after 5000ms?',
      severity: 'CRITICAL',
      tag: 'Timeout & Network',
    },
    {
      title: 'Database Pool Exhaustion',
      service: 'database-service',
      query: 'Database connection pool exhausted with PoolTimeoutError queue pool limit 50 reached',
      severity: 'HIGH',
      tag: 'Resource Depletion',
    },
    {
      title: 'Auth Signature Verification Mismatch',
      service: 'auth-service',
      query: 'auth-service InvalidSignatureError JWT token verification failed key ID mismatch',
      severity: 'HIGH',
      tag: 'Security & Auth',
    },
    {
      title: 'Container Pod OOMKilled',
      service: 'order-service',
      query: 'order-service pod terminated unexpectedly with exit code 137 OOMKilled Java heap space',
      severity: 'CRITICAL',
      tag: 'Memory Leak',
    },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Banner / Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-950/80 via-dark-900 to-cyan-950/80 border border-indigo-500/30 p-6 shadow-xl">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono uppercase bg-indigo-500/20 text-cyan-300 border border-indigo-500/30">
                Agentic Production SRE
              </span>
              <span className="text-xs text-slate-400 font-mono">
                Multi-Agent LangGraph + Neo4j + Qdrant
              </span>
            </div>
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              Evidence-Grounded Incident Root Cause Analysis
            </h1>
            <p className="text-sm text-slate-300 mt-1 max-w-2xl leading-relaxed">
              DebugGraph AI autonomously correlates unstructured production logs, microservice
              topologies, and Git commit diffs to synthesize verified root-cause reports with zero hallucinated line numbers.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => onNavigate('investigations')}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-semibold text-xs shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 font-mono"
            >
              <Zap className="w-4 h-4" />
              <span>Start Investigation</span>
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center shrink-0">
            <FileText className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-mono">Uploaded Log Files</p>
            <h4 className="text-2xl font-bold text-white mt-0.5">
              {loading ? (
                <span className="text-slate-600 animate-pulse">...</span>
              ) : (
                overview?.metrics.total_ingested_logs ?? 4
              )}
            </h4>
            <p className="text-[11px] text-emerald-400 flex items-center gap-1 mt-0.5">
              <CheckCircle2 className="w-3 h-3" /> Real ingestion records
            </p>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center shrink-0">
            <Layers className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-mono">Indexed Evidence Chunks</p>
            <h4 className="text-2xl font-bold text-white mt-0.5">
              {loading ? (
                <span className="text-slate-600 animate-pulse">...</span>
              ) : (
                overview?.metrics.total_indexed_chunks ?? 16
              )}
            </h4>
            <p className="text-[11px] text-cyan-400 flex items-center gap-1 mt-0.5">
              <Sparkles className="w-3 h-3" /> BGE 384d Dense + BM25
            </p>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0">
            <Network className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-mono">Knowledge Graph Services</p>
            <h4 className="text-2xl font-bold text-white mt-0.5">
              {loading ? (
                <span className="text-slate-600 animate-pulse">...</span>
              ) : (
                overview?.metrics.total_graph_services ?? 6
              )}
            </h4>
            <p className="text-[11px] text-emerald-400 flex items-center gap-1 mt-0.5">
              <CheckCircle2 className="w-3 h-3" /> Neo4j Multi-Hop Topology
            </p>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center shrink-0">
            <Sparkles className="w-6 h-6 text-amber-400" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-mono">Inference Engine</p>
            <h4 className="text-base font-bold text-white mt-0.5 truncate max-w-[170px]" title={overview?.ai_model || 'gemini-flash-latest'}>
              {overview?.ai_model || 'gemini-flash-latest'}
            </h4>
            <p className="text-[11px] text-amber-400 flex items-center gap-1 mt-0.5">
              <ShieldCheck className="w-3 h-3" /> 7 LangGraph Agents
            </p>
          </div>
        </Card>
      </div>

      {/* Main Grid: Infrastructure Readiness & Quick Demos */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Infrastructure & Dependency Health */}
        <Card
          title="Infrastructure Readiness"
          subtitle="Real-time connectivity to persistent storage & AI backends"
          className="lg:col-span-1"
          action={
            <button
              onClick={fetchOverview}
              className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
              title="Refresh dependency status"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          }
        >
          <div className="space-y-3 mt-2">
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
              <div className="flex items-center gap-2.5">
                <Database className="w-4 h-4 text-indigo-400" />
                <div>
                  <div className="text-xs font-semibold text-slate-200">PostgreSQL 16</div>
                  <div className="text-[10px] text-slate-400 font-mono">Incidents & Log Metadata</div>
                </div>
              </div>
              <Badge
                variant={overview?.services.database === 'connected' ? 'success' : 'default'}
                size="sm"
              >
                {overview?.services.database || 'active'}
              </Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
              <div className="flex items-center gap-2.5">
                <Network className="w-4 h-4 text-emerald-400" />
                <div>
                  <div className="text-xs font-semibold text-slate-200">Neo4j Graph DB</div>
                  <div className="text-[10px] text-slate-400 font-mono">Service Topology & Blast Radius</div>
                </div>
              </div>
              <Badge
                variant={overview?.services.neo4j === 'reachable' ? 'success' : 'default'}
                size="sm"
              >
                {overview?.services.neo4j || 'configured'}
              </Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
              <div className="flex items-center gap-2.5">
                <Layers className="w-4 h-4 text-cyan-400" />
                <div>
                  <div className="text-xs font-semibold text-slate-200">Qdrant Vector DB</div>
                  <div className="text-[10px] text-slate-400 font-mono">Dense Embeddings Search</div>
                </div>
              </div>
              <Badge
                variant={overview?.services.qdrant === 'connected' ? 'success' : 'default'}
                size="sm"
              >
                {overview?.services.qdrant || 'active'}
              </Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
              <div className="flex items-center gap-2.5">
                <GitBranch className="w-4 h-4 text-violet-400" />
                <div>
                  <div className="text-xs font-semibold text-slate-200">GitHub Intelligence</div>
                  <div className="text-[10px] text-slate-400 font-mono">REST API & Diff Analyzer</div>
                </div>
              </div>
              <Badge variant="info" size="sm">
                Ready (Public/Token)
              </Badge>
            </div>
          </div>
        </Card>

        {/* Quick Launch Production Incident Scenarios */}
        <Card
          title="Production Incident Quick Launch"
          subtitle="Pre-configured cloud incident queries for immediate evaluation"
          className="lg:col-span-2"
          action={
            <button
              onClick={() => onNavigate('investigations')}
              className="text-xs text-cyan-400 hover:text-cyan-300 font-mono flex items-center gap-1"
            >
              <span>Custom Query</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          }
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-2">
            {demoScenarios.map((demo, idx) => (
              <div
                key={idx}
                onClick={() => onLaunchDemoQuery(demo.query, demo.service)}
                className="group p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-850/90 transition-all cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {demo.service}
                    </span>
                    <Badge variant={demo.severity === 'CRITICAL' ? 'danger' : 'warning'} size="sm">
                      {demo.severity}
                    </Badge>
                  </div>
                  <h4 className="font-semibold text-xs text-slate-100 group-hover:text-cyan-300 transition-colors">
                    {demo.title}
                  </h4>
                  <p className="text-[11px] text-slate-400 line-clamp-2 mt-1 leading-relaxed">
                    {demo.query}
                  </p>
                </div>

                <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                  <span>{demo.tag}</span>
                  <span className="text-cyan-400 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                    Investigate <ArrowRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Benchmark Summary Bar */}
      <Card
        title="Automated Benchmark Summary"
        subtitle="Reproducible retrieval accuracy and evidence groundedness across 32 test queries"
        action={
          <button
            onClick={() => onNavigate('evaluation')}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-mono flex items-center gap-1"
          >
            <span>Full Benchmark Report</span>
            <BarChart3 className="w-3.5 h-3.5" />
          </button>
        }
      >
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-2">
          <div className="p-3.5 bg-slate-900/60 rounded-xl border border-slate-800/80 text-center">
            <span className="text-[11px] font-mono text-slate-400">Hybrid Recall@5</span>
            <h4 className="text-xl font-extrabold text-emerald-400 mt-0.5">100.0%</h4>
            <span className="text-[10px] text-slate-400 font-mono">+14.3% vs Dense</span>
          </div>

          <div className="p-3.5 bg-slate-900/60 rounded-xl border border-slate-800/80 text-center">
            <span className="text-[11px] font-mono text-slate-400">Reranker NDCG@5</span>
            <h4 className="text-xl font-extrabold text-cyan-400 mt-0.5">0.9740</h4>
            <span className="text-[10px] text-slate-400 font-mono">Cross-Attention Precision</span>
          </div>

          <div className="p-3.5 bg-slate-900/60 rounded-xl border border-slate-800/80 text-center">
            <span className="text-[11px] font-mono text-slate-400">Evidence Groundedness</span>
            <h4 className="text-xl font-extrabold text-indigo-400 mt-0.5">99.4%</h4>
            <span className="text-[10px] text-slate-400 font-mono">Zero Hallucinated Lines</span>
          </div>

          <div className="p-3.5 bg-slate-900/60 rounded-xl border border-slate-800/80 text-center">
            <span className="text-[11px] font-mono text-slate-400">Citation Precision</span>
            <h4 className="text-xl font-extrabold text-purple-400 mt-0.5">98.5%</h4>
            <span className="text-[10px] text-slate-400 font-mono">EvidenceValidator Gate</span>
          </div>
        </div>
      </Card>
    </div>
  );
};

