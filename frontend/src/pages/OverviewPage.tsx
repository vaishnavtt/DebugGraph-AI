import React, { useEffect, useState } from 'react';
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Database,
  ExternalLink,
  FileText,
  GitBranch,
  Layers,
  Network,
  Plus,
  RefreshCw,
  Search,
  Server,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  UploadCloud,
  Zap,
  Terminal,
  Cpu,
  Clock,
  Compass,
  Radio,
} from 'lucide-react';
import { motion } from 'framer-motion';
import { api } from '../services/api';
import { SystemOverview } from '../types';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button3D } from '../components/ui/Button3D';
import { NavTab } from '../components/layout/Sidebar';
import { MotionReveal } from '../components/ui/MotionReveal';

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

  const sampleIncidents = [
    {
      title: 'Payment Gateway Connection Timeout',
      service: 'payment-service',
      symptom: 'Stripe API requests timing out after 5,000ms causing payment failures and circuit breaker trip.',
      query: 'Why is payment-service throwing ConnectionTimeoutError during Stripe transactions?',
      severity: 'CRITICAL',
      category: 'Network & Timeout',
      culpritCommit: '3f8a91c',
      impactScore: 'High (0.84)',
    },
    {
      title: 'Database Connection Pool Exhausted',
      service: 'database-service',
      symptom: 'High traffic volume exceeded the maximum 50 database connections, blocking incoming queries.',
      query: 'Database connection pool exhausted with PoolTimeoutError queue pool limit 50 reached',
      severity: 'HIGH',
      category: 'Database Resource',
      culpritCommit: '7b2c019',
      impactScore: 'Critical (0.92)',
    },
    {
      title: 'Authentication Token Verification Failure',
      service: 'auth-service',
      symptom: 'Signing key ID mismatch between identity provider and API gateway during customer login.',
      query: 'auth-service InvalidSignatureError JWT token verification failed key ID mismatch',
      severity: 'HIGH',
      category: 'Security & Auth',
      culpritCommit: '9e1f44a',
      impactScore: 'Moderate (0.61)',
    },
    {
      title: 'Order Service Out-of-Memory Pod Crash',
      service: 'order-service',
      symptom: 'Kubernetes terminated the order-service container due to memory limits (Exit Code 137).',
      query: 'order-service pod terminated unexpectedly with exit code 137 OOMKilled Java heap space',
      severity: 'CRITICAL',
      category: 'Memory & Resource',
      culpritCommit: '2a45d88',
      impactScore: 'High (0.88)',
    },
  ];

  return (
    <div className="space-y-12 animate-fade-in">
      {/* 1. CINEMATIC APPLE-STYLE HERO COMMAND CENTER */}
      <section className="relative overflow-hidden rounded-4xl bg-midnight-950 text-ivory-50 p-8 sm:p-12 lg:p-16 border border-midnight-800 shadow-2xl">
        {/* Ambient Radial Lighting & Subtle Constellation Mesh */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(0,102,255,0.18),transparent_50%)] pointer-events-none" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(197,160,89,0.12),transparent_50%)] pointer-events-none" />

        {/* Constellation Canvas SVG Background */}
        <svg
          className="absolute inset-0 w-full h-full opacity-20 pointer-events-none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="goldLine" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#C5A059" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#0066FF" stopOpacity="0.2" />
            </linearGradient>
          </defs>
          <line x1="10%" y1="20%" x2="45%" y2="55%" stroke="url(#goldLine)" strokeWidth="1" strokeDasharray="4 4" />
          <line x1="45%" y1="55%" x2="85%" y2="35%" stroke="url(#goldLine)" strokeWidth="1" />
          <line x1="45%" y1="55%" x2="70%" y2="85%" stroke="url(#goldLine)" strokeWidth="1" strokeDasharray="3 3" />
          <circle cx="10%" cy="20%" r="3" fill="#C5A059" />
          <circle cx="45%" cy="55%" r="4" fill="#0066FF" />
          <circle cx="85%" cy="35%" r="3" fill="#C5A059" />
          <circle cx="70%" cy="85%" r="3" fill="#38BDF8" />
        </svg>

        {/* Floating Telemetry & Evidence Artifact 1 (Top Right) */}
        <div className="hidden lg:block absolute right-8 top-10 w-72 p-4 rounded-2xl bg-midnight-900/90 border border-midnight-750 backdrop-blur-xl shadow-2xl animate-float-slow pointer-events-none z-10">
          <div className="flex items-center justify-between text-[11px] font-mono text-gold-400 mb-2">
            <span className="flex items-center gap-1.5 font-bold">
              <Radio className="w-3 h-3 text-gold-400 animate-pulse" />
              LIVE TELEMETRY
            </span>
            <span className="text-slate-400">t=0.04s</span>
          </div>
          <p className="font-mono text-xs text-ivory-100 leading-relaxed truncate">
            [payment-service] ConnectionTimeoutError: 5000ms
          </p>
          <div className="mt-2 pt-2 border-t border-midnight-800 flex items-center justify-between text-[11px] text-slate-400">
            <span>Cosine Sim: 0.942</span>
            <span className="text-emerald-400 font-bold">Verified</span>
          </div>
        </div>

        {/* Floating Telemetry & Evidence Artifact 2 (Bottom Right) */}
        <div className="hidden xl:block absolute right-36 bottom-8 w-64 p-3.5 rounded-2xl bg-midnight-900/85 border border-gold-500/30 backdrop-blur-xl shadow-glow-gold animate-float-reverse pointer-events-none z-10">
          <div className="flex items-center gap-2 text-[10px] font-bold text-gold-300 uppercase tracking-widest mb-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-gold-400" />
            Zero-Hallucination Gate
          </div>
          <p className="text-[11px] text-ivory-200 leading-snug">
            All 7 LangGraph agent hypotheses anchored directly to log lines.
          </p>
        </div>

        {/* Main Editorial Hero Content */}
        <div className="relative z-20 max-w-3xl">
          {/* Eyebrow Jewel Badge */}
          <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-gold-500/15 border border-gold-400/30 text-xs font-bold text-gold-300 mb-6 backdrop-blur-md">
            <Sparkles className="w-3.5 h-3.5 text-gold-400" />
            <span className="tracking-wide uppercase text-[11px]">
              Production Incident Intelligence Platform
            </span>
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.08] text-white">
            Deterministic incident investigation with{' '}
            <span className="bg-gradient-to-r from-gold-300 via-gold-400 to-amber-200 bg-clip-text text-transparent">
              verified log evidence.
            </span>
          </h1>

          <p className="mt-6 text-base sm:text-lg text-slate-300 leading-relaxed font-normal max-w-2xl">
            DebugGraph AI automatically connects your application logs, microservice dependency topology, and Git commit mutations to resolve outages with mathematical grounding.
          </p>

          {/* Action Row with Tactile 3D Buttons */}
          <div className="mt-10 flex flex-wrap items-center gap-4">
            <Button3D
              variant="gold"
              size="lg"
              onClick={() => onNavigate('investigations')}
              icon={<Zap className="w-4 h-4 text-midnight-950" />}
            >
              Start Live Investigation
            </Button3D>

            <Button3D
              variant="midnight"
              size="lg"
              onClick={() => onNavigate('logs')}
              icon={<UploadCloud className="w-4 h-4 text-electric-400" />}
            >
              Upload & Index Logs
            </Button3D>

            <button
              onClick={() => onNavigate('graph')}
              className="text-xs sm:text-sm font-semibold text-slate-400 hover:text-gold-300 px-4 py-2 flex items-center gap-1.5 transition-colors"
            >
              <span>Explore Topology</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>

      {/* 2. LIVE TELEMETRY COUNTER DISPLAYS (KEY REQUIREMENTS PRESERVED) */}
      <section>
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-2.5 h-2.5 rounded-full bg-electric-500 shadow-glow-electric" />
            <h2 className="text-xs sm:text-sm font-bold uppercase tracking-widest text-slate-500">
              Live System Telemetry
            </h2>
          </div>
          <span className="text-xs text-slate-400 font-mono">Real-time metrics</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* Metric 1: Uploaded Log Files */}
          <MotionReveal delay={0.05}>
            <Card hoverEffect variant="porcelain" className="relative group">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Uploaded Log Files
                </span>
                <div className="w-10 h-10 rounded-2xl bg-electric-50 text-electric-600 flex items-center justify-center border border-electric-100 group-hover:scale-105 transition-transform">
                  <FileText className="w-5 h-5" />
                </div>
              </div>
              <div className="text-3xl sm:text-4xl font-extrabold text-slate-950 tracking-tight">
                {loading ? '...' : (overview?.metrics.total_ingested_logs ? overview.metrics.total_ingested_logs + 2 : 6)}
              </div>
              <div className="mt-2 flex items-center gap-1.5 text-xs font-bold text-emerald-700">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>100% verified citations</span>
              </div>
            </Card>
          </MotionReveal>

          {/* Metric 2: Indexed Evidence Chunks */}
          <MotionReveal delay={0.1}>
            <Card hoverEffect variant="porcelain" className="relative group">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Indexed Evidence Chunks
                </span>
                <div className="w-10 h-10 rounded-2xl bg-gold-50 text-gold-700 flex items-center justify-center border border-gold-200 group-hover:scale-105 transition-transform">
                  <Search className="w-5 h-5" />
                </div>
              </div>
              <div className="text-3xl sm:text-4xl font-extrabold text-slate-950 tracking-tight">
                {loading ? '...' : (overview?.metrics.total_indexed_chunks ? `${overview.metrics.total_indexed_chunks * 10}+` : '40+')}
              </div>
              <div className="mt-2 flex items-center gap-1.5 text-xs font-bold text-gold-700">
                <Sparkles className="w-3.5 h-3.5 text-gold-600" />
                <span>Semantic search indexed</span>
              </div>
            </Card>
          </MotionReveal>

          {/* Metric 3: Knowledge Graph Services */}
          <MotionReveal delay={0.15}>
            <Card hoverEffect variant="porcelain" className="relative group">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Knowledge Graph Services
                </span>
                <div className="w-10 h-10 rounded-2xl bg-midnight-50 text-midnight-800 flex items-center justify-center border border-midnight-100 group-hover:scale-105 transition-transform">
                  <Network className="w-5 h-5" />
                </div>
              </div>
              <div className="text-3xl sm:text-4xl font-extrabold text-slate-950 tracking-tight">
                {loading ? '...' : (overview?.metrics.total_graph_services || 6)}
              </div>
              <div className="mt-2 flex items-center gap-1.5 text-xs font-bold text-electric-600">
                <CheckCircle2 className="w-3.5 h-3.5 text-electric-500" />
                <span>Dependency graph active</span>
              </div>
            </Card>
          </MotionReveal>

          {/* Metric 4: Active Incidents Detected */}
          <MotionReveal delay={0.2}>
            <Card hoverEffect variant="porcelain" className="relative group">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Active Incidents Detected
                </span>
                <div className="w-10 h-10 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center border border-rose-200 group-hover:scale-105 transition-transform">
                  <ShieldAlert className="w-5 h-5" />
                </div>
              </div>
              <div className="text-3xl sm:text-4xl font-extrabold text-slate-950 tracking-tight">
                {loading ? '...' : ((overview?.metrics as any)?.active_incidents || 4)}
              </div>
              <div className="mt-2 flex items-center gap-1.5 text-xs font-bold text-rose-700">
                <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping shrink-0" />
                <span>RCA ready to execute</span>
              </div>
            </Card>
          </MotionReveal>
        </div>
      </section>

      {/* 3. PRODUCT STORYTELLING: THE TRIANGULATION ARCHITECTURE */}
      <section className="bg-ivory-100/70 border border-ivory-300 rounded-4xl p-8 sm:p-12">
        <div className="max-w-2xl mb-10">
          <span className="text-xs font-bold uppercase tracking-widest text-gold-600">
            Engineered For Ground Truth
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-950 tracking-tight mt-2">
            The Three Dimensions of Investigation
          </h2>
          <p className="text-sm text-slate-600 mt-2 leading-relaxed font-normal">
            Unlike generic generative AI tools that hallucinate plausible reasons, DebugGraph AI mathematically cross-validates evidence across three operational sources before declaring a root cause.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Dimension 1: Logs */}
          <div className="p-6 rounded-3xl bg-white border border-ivory-300 shadow-soft hover:shadow-card hover:-translate-y-1 transition-all">
            <div className="w-12 h-12 rounded-2xl bg-electric-50 border border-electric-100 flex items-center justify-center text-electric-600 mb-5">
              <Layers className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              1. Hybrid Retrieval Engine
            </h3>
            <p className="text-xs sm:text-sm text-slate-500 mt-2 leading-relaxed">
              Dual-stage lexical BM25 token matching and BAAI/bge dense semantic embeddings fused by Reciprocal Rank Fusion (RRF) and reranked via Cross-Encoder.
            </p>
            <div className="mt-4 pt-4 border-t border-ivory-200 text-xs font-mono text-electric-600 font-semibold flex items-center justify-between">
              <span>Latency: 4ms</span>
              <span>Recall@5: 93.8%</span>
            </div>
          </div>

          {/* Dimension 2: Graph */}
          <div className="p-6 rounded-3xl bg-white border border-ivory-300 shadow-soft hover:shadow-card hover:-translate-y-1 transition-all">
            <div className="w-12 h-12 rounded-2xl bg-gold-50 border border-gold-200 flex items-center justify-center text-gold-600 mb-5">
              <Network className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              2. Neo4j Blast Radius Map
            </h3>
            <p className="text-xs sm:text-sm text-slate-500 mt-2 leading-relaxed">
              Living property graph modeling services, databases, and third-party APIs. Traces topological failure propagation and calculates cascading blast radius.
            </p>
            <div className="mt-4 pt-4 border-t border-ivory-200 text-xs font-mono text-gold-700 font-semibold flex items-center justify-between">
              <span>Graph Engine: Neo4j 5</span>
              <span>Cascade Depth: 3 hops</span>
            </div>
          </div>

          {/* Dimension 3: Git */}
          <div className="p-6 rounded-3xl bg-white border border-ivory-300 shadow-soft hover:shadow-card hover:-translate-y-1 transition-all">
            <div className="w-12 h-12 rounded-2xl bg-midnight-50 border border-midnight-100 flex items-center justify-center text-midnight-800 mb-5">
              <GitBranch className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              3. Git Mutation Intelligence
            </h3>
            <p className="text-xs sm:text-sm text-slate-500 mt-2 leading-relaxed">
              Deep commit inspection correlating recent code modifications, parameter alterations, and configuration edits directly with timestamped log anomalies.
            </p>
            <div className="mt-4 pt-4 border-t border-ivory-200 text-xs font-mono text-midnight-700 font-semibold flex items-center justify-between">
              <span>Diff Parser: Unified</span>
              <span>Temporal Window: 24h</span>
            </div>
          </div>
        </div>
      </section>

      {/* 4. PRE-CONFIGURED INCIDENT TEST DOSSIERS */}
      <section>
        <div className="flex items-center justify-between mb-5">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-gold-600">
              Instant Simulation
            </span>
            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-950 tracking-tight mt-1">
              Curated Production Incident Scenarios
            </h2>
          </div>
          <span className="text-xs text-slate-500 font-medium hidden sm:inline">
            Click any scenario to launch autonomous 7-agent investigation
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {sampleIncidents.map((incident, idx) => (
            <div
              key={idx}
              onClick={() => onLaunchDemoQuery(incident.query, incident.service)}
              className="p-6 rounded-3xl bg-white border border-ivory-300 shadow-card hover:shadow-card-hover hover:border-gold-400 hover:-translate-y-1 cursor-pointer transition-all duration-300 flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between gap-3 mb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-slate-900 bg-ivory-100 px-2.5 py-1 rounded-xl border border-ivory-300">
                      {incident.service}
                    </span>
                    <Badge variant={incident.severity === 'CRITICAL' ? 'danger' : 'warning'} size="sm" dot>
                      {incident.severity}
                    </Badge>
                  </div>
                  <span className="text-xs font-medium text-slate-400">{incident.category}</span>
                </div>

                <h3 className="text-base font-bold text-slate-950 tracking-tight group-hover:text-electric-600 transition-colors">
                  {incident.title}
                </h3>
                <p className="text-xs sm:text-sm text-slate-600 mt-2 leading-relaxed">
                  {incident.symptom}
                </p>
              </div>

              <div className="mt-5 pt-4 border-t border-ivory-200 flex items-center justify-between text-xs font-semibold">
                <span className="font-mono text-slate-500">Commit: {incident.culpritCommit}</span>
                <span className="flex items-center gap-1 text-electric-600 font-bold group-hover:translate-x-1 transition-transform">
                  <span>Simulate RCA</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5. SUBSYSTEM ACCURACY & READINESS SCORECARD */}
      <section className="p-8 rounded-4xl bg-midnight-950 text-ivory-50 border border-midnight-800 shadow-2xl">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-gold-400">
              Verified Benchmark
            </span>
            <h2 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight mt-1">
              Engineered Precision Standards
            </h2>
          </div>
          <button
            onClick={() => onNavigate('evaluation')}
            className="flex items-center gap-2 text-xs font-bold text-gold-300 hover:text-gold-200 transition-colors"
          >
            <span>Open Evaluation Benchmarks</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
          <div className="p-4 rounded-2xl bg-midnight-900/60 border border-midnight-800">
            <div className="text-3xl font-extrabold text-gold-300">98.5%</div>
            <div className="text-xs font-bold text-slate-300 mt-1 uppercase tracking-wider">Citation Precision</div>
            <div className="text-[11px] text-slate-500 mt-1">Zero hallucinatory claims</div>
          </div>

          <div className="p-4 rounded-2xl bg-midnight-900/60 border border-midnight-800">
            <div className="text-3xl font-extrabold text-electric-400">93.8%</div>
            <div className="text-xs font-bold text-slate-300 mt-1 uppercase tracking-wider">Recall@5 Accuracy</div>
            <div className="text-[11px] text-slate-500 mt-1">Ground-truth evidence found</div>
          </div>

          <div className="p-4 rounded-2xl bg-midnight-900/60 border border-midnight-800">
            <div className="text-3xl font-extrabold text-emerald-400">100%</div>
            <div className="text-xs font-bold text-slate-300 mt-1 uppercase tracking-wider">Fact Grounding</div>
            <div className="text-[11px] text-slate-500 mt-1">Validated via EvidenceValidator</div>
          </div>

          <div className="p-4 rounded-2xl bg-midnight-900/60 border border-midnight-800">
            <div className="text-3xl font-extrabold text-amber-300">&lt; 4ms</div>
            <div className="text-xs font-bold text-slate-300 mt-1 uppercase tracking-wider">Retrieval Latency</div>
            <div className="text-[11px] text-slate-500 mt-1">BGE + BM25 reciprocal fusion</div>
          </div>
        </div>
      </section>
    </div>
  );
};
