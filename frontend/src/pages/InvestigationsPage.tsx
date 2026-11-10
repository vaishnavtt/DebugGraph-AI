import React, { useState } from 'react';
import {
  AlertCircle,
  AlertOctagon,
  AlertTriangle,
  ArrowRight,
  Bot,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Compass,
  Copy,
  ExternalLink,
  FileCode,
  FileSearch,
  FileText,
  Filter,
  GitCommit,
  Info,
  Layers,
  Network,
  Play,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Terminal,
  Wrench,
  Zap,
} from 'lucide-react';
import { api } from '../services/api';
import {
  InvestigationRequest,
  InvestigationResponse,
  PotentialRootCause,
  SupportingEvidenceItem,
} from '../types';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button3D } from '../components/ui/Button3D';
import { MultiAgentTimeline } from '../components/investigation/MultiAgentTimeline';

interface InvestigationsPageProps {
  initialQuery?: string;
  initialService?: string;
}

export const InvestigationsPage: React.FC<InvestigationsPageProps> = ({
  initialQuery = '',
  initialService = '',
}) => {
  // Query Form State
  const [query, setQuery] = useState(
    initialQuery ||
      'Why is payment-service throwing ConnectionTimeoutError during Stripe transactions?'
  );
  const [serviceName, setServiceName] = useState(initialService || 'payment-service');
  const [severity, setSeverity] = useState<string>('ERROR');
  const [topK, setTopK] = useState<number>(10);
  const [investigationMode, setInvestigationMode] = useState<'agentic' | 'standard'>('agentic');

  // Investigation Execution State
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<InvestigationResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'five_questions' | 'evidence' | 'timeline' | 'graph' | 'github'>('five_questions');
  const [expandedChunkId, setExpandedChunkId] = useState<string | null>(null);
  const [showAdvancedJson, setShowAdvancedJson] = useState<boolean>(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Quick scenario chips
  const quickScenarios = [
    {
      label: 'Stripe Gateway Timeout',
      query: 'Why is payment-service throwing ConnectionTimeoutError during Stripe transactions?',
      service: 'payment-service',
    },
    {
      label: 'Database Pool Exhausted',
      query: 'Database connection pool exhausted with PoolTimeoutError queue pool limit 50 reached',
      service: 'database-service',
    },
    {
      label: 'JWT Auth Verification Error',
      query: 'auth-service InvalidSignatureError JWT token verification failed key ID mismatch',
      service: 'auth-service',
    },
    {
      label: 'OOM Pod Termination',
      query: 'order-service pod terminated unexpectedly with exit code 137 OOMKilled Java heap space',
      service: 'order-service',
    },
  ];

  const handleInvestigate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const payload: InvestigationRequest = {
        query: query.trim(),
        service_name: serviceName.trim() || undefined,
        severity: severity || undefined,
        top_k: topK,
        rerank: true,
      };

      let response: InvestigationResponse;
      if (investigationMode === 'agentic') {
        response = await api.runAgenticInvestigation(payload);
      } else {
        response = await api.runStandardInvestigation(payload);
      }

      setResult(response);
      setActiveTab('five_questions');
      if (response.supporting_evidence.length > 0) {
        setExpandedChunkId(response.supporting_evidence[0].chunk_id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to complete incident investigation');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getSeverityBadge = (sev: string) => {
    const s = sev?.toUpperCase();
    if (s === 'CRITICAL') return <Badge variant="danger" dot>CRITICAL</Badge>;
    if (s === 'HIGH') return <Badge variant="danger" dot>HIGH SEVERITY</Badge>;
    if (s === 'MEDIUM' || s === 'WARN') return <Badge variant="warning" dot>MEDIUM</Badge>;
    return <Badge variant="info" dot>{sev || 'LOW'}</Badge>;
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* 1. START NEW INVESTIGATION COCKPIT CARD */}
      <Card
        title="Incident Investigation Workspace"
        subtitle="Describe the symptom or error in plain English. The AI agent team will search the logs, verify the root cause, and formulate solutions."
        icon={<Sparkles className="w-5 h-5 text-gold-600" />}
        variant="porcelain"
      >
        <form onSubmit={handleInvestigate} className="space-y-5">
          {/* Quick Scenario Chips */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Quick Test Scenarios:
            </span>
            {quickScenarios.map((sc, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuery(sc.query);
                  setServiceName(sc.service);
                }}
                className="text-xs px-3 py-1.5 rounded-xl bg-ivory-100 hover:bg-gold-50 text-slate-700 hover:text-gold-900 border border-ivory-300 hover:border-gold-300 transition-all font-semibold"
              >
                {sc.label}
              </button>
            ))}
          </div>

          {/* Natural Language Query Input */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
              Incident Symptom or Error Message <span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={3}
                placeholder="e.g. Why is payment-service throwing ConnectionTimeoutError during Stripe checkout?"
                className="w-full bg-ivory-50/70 border border-ivory-300 rounded-2xl px-4 py-3.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gold-500/30 focus:border-gold-500 transition-all resize-none font-normal"
                required
              />
              <div className="absolute right-3.5 bottom-3.5 text-[11px] text-slate-400 font-mono">
                {query.length} chars
              </div>
            </div>
          </div>

          {/* Filter Controls Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Investigation Mode Selector */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                Investigation Mode
              </label>
              <div className="grid grid-cols-2 gap-1.5 p-1 bg-ivory-100 rounded-xl border border-ivory-300">
                <button
                  type="button"
                  onClick={() => setInvestigationMode('agentic')}
                  className={`py-2 text-xs font-bold rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                    investigationMode === 'agentic'
                      ? 'bg-midnight-950 text-gold-300 shadow-sm border border-gold-500/40'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Bot className="w-3.5 h-3.5 text-gold-400" />
                  <span>7 Agents</span>
                </button>
                <button
                  type="button"
                  onClick={() => setInvestigationMode('standard')}
                  className={`py-2 text-xs font-bold rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                    investigationMode === 'standard'
                      ? 'bg-midnight-950 text-gold-300 shadow-sm border border-gold-500/40'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Zap className="w-3.5 h-3.5 text-amber-400" />
                  <span>Single-Pass</span>
                </button>
              </div>
            </div>

            {/* Microservice Name Filter */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                Target Service (Optional)
              </label>
              <input
                type="text"
                value={serviceName}
                onChange={(e) => setServiceName(e.target.value)}
                placeholder="e.g. payment-service"
                className="w-full bg-ivory-50/70 border border-ivory-300 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gold-500/30 focus:border-gold-500 transition-all font-medium"
              />
            </div>

            {/* Severity Filter */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                Log Severity Filter
              </label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="w-full bg-ivory-50/70 border border-ivory-300 rounded-xl px-3 py-2.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-gold-500/30 focus:border-gold-500 transition-all font-medium"
              >
                <option value="">All Severities</option>
                <option value="CRITICAL">Critical Only</option>
                <option value="ERROR">Error & Above</option>
                <option value="WARN">Warning & Above</option>
                <option value="INFO">Information</option>
              </select>
            </div>

            {/* Evidence Candidates Slider */}
            <div>
              <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                <span>Evidence Limit</span>
                <span className="font-mono text-electric-600 font-bold">{topK} chunks</span>
              </div>
              <input
                type="range"
                min="3"
                max="30"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full accent-electric-600 cursor-pointer h-2 bg-ivory-200 rounded-lg mt-2"
              />
            </div>
          </div>

          {/* Action Row with 3D Button */}
          <div className="flex items-center justify-between pt-4 border-t border-ivory-200 flex-wrap gap-4">
            <div className="text-xs text-slate-500 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>Evidence grounding automatically prevents AI hallucinations</span>
            </div>

            <Button3D
              variant="gold"
              size="md"
              type="submit"
              disabled={loading || !query.trim()}
              loading={loading}
              icon={<Sparkles className="w-4 h-4 text-midnight-950" />}
            >
              <span>Execute Multi-Agent RCA</span>
            </Button3D>
          </div>
        </form>
      </Card>

      {/* 2. LOADING STATE ANIMATION */}
      {loading && (
        <Card className="text-center py-16" variant="porcelain">
          <div className="w-20 h-20 rounded-3xl bg-midnight-950 border border-gold-400/40 flex items-center justify-center mx-auto mb-6 shadow-glow-gold animate-pulse">
            <Sparkles className="w-10 h-10 text-gold-400 animate-spin" />
          </div>
          <h3 className="text-lg font-extrabold text-slate-950 tracking-tight">
            LangGraph Multi-Agent Team Investigating Incident
          </h3>
          <p className="text-xs sm:text-sm text-slate-500 mt-2 max-w-lg mx-auto leading-relaxed">
            Supervisor is dispatching Log Investigator, Graph Navigator, and Git Inspector to establish verified causal evidence without hallucinations...
          </p>
        </Card>
      )}

      {/* 3. ERROR BANNER */}
      {error && (
        <div className="p-5 bg-rose-50 border border-rose-200 rounded-3xl text-rose-900 text-xs sm:text-sm font-semibold flex items-center justify-between animate-fade-in shadow-soft">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-700 font-bold ml-4 hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* 4. INVESTIGATION RESULTS DOSSIER */}
      {result && !loading && (
        <div className="space-y-8 animate-fade-in">
          {/* Executive Summary Header Panel */}
          <div className="p-6 sm:p-8 rounded-4xl bg-midnight-950 text-ivory-50 border border-midnight-800 shadow-2xl relative overflow-hidden">
            <div className="absolute right-0 top-0 w-80 h-80 rounded-full bg-gold-500/10 blur-3xl pointer-events-none" />

            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 relative z-10">
              <div className="space-y-3 max-w-3xl">
                <div className="flex items-center gap-3 flex-wrap">
                  <Badge variant={result.severity_assessment === 'CRITICAL' ? 'danger' : 'warning'} size="md" dot>
                    {result.severity_assessment}
                  </Badge>
                  <span className="text-xs font-mono text-gold-400">
                    ID: {result.investigation_id}
                  </span>
                  <span className="text-xs text-slate-400">
                    Target: <strong className="text-ivory-100 font-mono">{result.affected_services[0] || 'payment-service'}</strong>
                  </span>
                </div>

                <h2 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight leading-snug">
                  {result.incident_summary}
                </h2>
              </div>

              {/* Status Counters */}
              <div className="grid grid-cols-2 gap-3 shrink-0">
                <div className="p-3.5 bg-midnight-900 rounded-2xl border border-midnight-800 text-center">
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Evidence Status</span>
                  <p className="text-xs sm:text-sm font-extrabold text-emerald-400 mt-1">
                    {result.evidence_sufficiency.status} ({(result.evidence_sufficiency.confidence_score * 100).toFixed(0)}%)
                  </p>
                </div>
                <div className="p-3.5 bg-midnight-900 rounded-2xl border border-midnight-800 text-center">
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Reasoning Engine</span>
                  <p className="text-xs sm:text-sm font-extrabold text-gold-300 mt-1 truncate max-w-[130px]" title={result.model_information.model_name}>
                    {result.model_information.model_name}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Tabs for Investigation */}
          <div className="flex items-center gap-2 border-b border-ivory-300 pb-2 overflow-x-auto">
            {[
              { id: 'five_questions' as const, label: 'Investigation Report', icon: Sparkles },
              { id: 'evidence' as const, label: `Source Evidence (${result.supporting_evidence.length})`, icon: FileText },
              { id: 'timeline' as const, label: `Agent Steps & Trace (${result.agent_execution_trace?.length || 0})`, icon: Bot },
              { id: 'graph' as const, label: 'Service Blast Radius', icon: Network },
              { id: 'github' as const, label: 'GitHub Commits', icon: GitCommit },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl text-xs sm:text-sm font-bold whitespace-nowrap transition-all ${
                    isActive
                      ? 'bg-midnight-950 text-gold-300 shadow-sm border border-gold-500/40'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-ivory-200/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-gold-400' : 'text-slate-400'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* TAB 1: 5 UNDERSTANDABLE SECTIONS (WHAT, WHY, EVIDENCE, IMPACT, ACTIONS) */}
          {activeTab === 'five_questions' && (
            <div className="space-y-6">
              {/* SECTION 1: WHAT HAPPENED? */}
              <Card
                title="1. What happened?"
                subtitle="High-level incident summary and observed symptoms"
                icon={<Info className="w-5 h-5 text-electric-600" />}
                variant="porcelain"
              >
                <div className="p-5 rounded-2xl bg-ivory-100/70 border border-ivory-300 space-y-4">
                  <p className="text-sm sm:text-base text-slate-800 leading-relaxed font-normal">
                    {result.incident_summary}
                  </p>

                  {result.key_observations.length > 0 && (
                    <div className="space-y-2.5 pt-3 border-t border-ivory-200">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-700 block">
                        Observed Facts & Telemetry:
                      </span>
                      {result.key_observations.map((obs, idx) => (
                        <div key={idx} className="flex items-start gap-3 text-xs sm:text-sm text-slate-700">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                          <span>{obs.observation}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </Card>

              {/* SECTION 2: WHY DID IT HAPPEN? */}
              <Card
                title="2. Why did it happen?"
                subtitle="Ranked root-cause explanations verified against application logs"
                icon={<Sparkles className="w-5 h-5 text-gold-600" />}
                variant="porcelain"
              >
                <div className="space-y-4">
                  {result.potential_root_causes.map((rc, idx) => (
                    <div
                      key={idx}
                      className="p-5 rounded-2xl bg-white border border-ivory-300 shadow-soft space-y-3 hover:border-gold-300 transition-all"
                    >
                      <div className="flex items-center justify-between gap-3 flex-wrap">
                        <div className="flex items-center gap-2.5">
                          <span className="w-7 h-7 rounded-xl bg-gold-100 text-gold-800 border border-gold-300 text-xs font-extrabold flex items-center justify-center">
                            #{rc.rank}
                          </span>
                          <h4 className="font-bold text-sm sm:text-base text-slate-950">
                            {rc.hypothesis}
                          </h4>
                        </div>
                        <Badge
                          variant={
                            rc.confidence === 'HIGH'
                              ? 'success'
                              : rc.confidence === 'MEDIUM'
                              ? 'warning'
                              : 'default'
                          }
                          size="md"
                          dot
                        >
                          {rc.confidence} Confidence
                        </Badge>
                      </div>

                      <p className="text-xs sm:text-sm text-slate-700 leading-relaxed">
                        {rc.reasoning}
                      </p>

                      {rc.confidence_reasoning && (
                        <div className="p-3.5 bg-ivory-100 rounded-xl border border-ivory-200 text-xs text-slate-700">
                          <span className="font-bold text-slate-900">Verification Rationale: </span>
                          {rc.confidence_reasoning}
                        </div>
                      )}

                      {rc.supporting_evidence_ids.length > 0 && (
                        <div className="flex items-center gap-2 flex-wrap pt-1 text-xs">
                          <span className="text-slate-500 font-semibold">Cited Log Evidence:</span>
                          {rc.supporting_evidence_ids.map((cid) => (
                            <button
                              key={cid}
                              onClick={() => {
                                setActiveTab('evidence');
                                setExpandedChunkId(cid);
                              }}
                              className="px-2.5 py-1 rounded-lg bg-gold-50 text-gold-800 border border-gold-300 text-[11px] font-mono font-bold hover:bg-gold-100 transition-colors"
                            >
                              {cid}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </Card>

              {/* SECTION 3: WHAT EVIDENCE WAS FOUND? */}
              <Card
                title="3. What evidence was found?"
                subtitle="Exact log excerpts cited by the AI to support this root cause diagnosis"
                icon={<FileText className="w-5 h-5 text-electric-600" />}
                variant="porcelain"
                action={
                  <button
                    onClick={() => setActiveTab('evidence')}
                    className="text-xs text-electric-600 hover:text-electric-800 font-bold flex items-center gap-1"
                  >
                    <span>View all {result.supporting_evidence.length} excerpts</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                }
              >
                <div className="space-y-4">
                  {result.supporting_evidence.slice(0, 2).map((ev, idx) => (
                    <div
                      key={idx}
                      className="p-5 bg-midnight-950 text-ivory-50 rounded-2xl border border-midnight-800 space-y-3"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2 font-mono text-gold-300 font-bold">
                          <FileCode className="w-4 h-4 text-electric-400" />
                          <span>{ev.source_filename || 'application.log'}</span>
                          <span className="text-slate-400 font-normal">
                            (lines {ev.source_line_start}-{ev.source_line_end})
                          </span>
                        </div>
                        <Badge variant={ev.severity === 'ERROR' ? 'danger' : 'info'} size="sm">
                          {ev.severity || 'LOG'}
                        </Badge>
                      </div>

                      <pre className="p-4 bg-midnight-900 rounded-xl border border-midnight-800 text-xs font-mono text-ivory-100 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                        {ev.relevant_excerpt}
                      </pre>
                    </div>
                  ))}
                </div>
              </Card>

              {/* SECTION 4: WHICH SERVICES ARE AFFECTED? */}
              <Card
                title="4. Which services are affected?"
                subtitle="Microservice impact analysis and cascade blast radius"
                icon={<Network className="w-5 h-5 text-midnight-800" />}
                variant="porcelain"
              >
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                  <div className="p-5 rounded-2xl bg-ivory-100 border border-ivory-300 text-center">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block">Primary Service</span>
                    <h4 className="text-lg font-extrabold text-slate-950 mt-1 font-mono">
                      {result.affected_services[0] || 'Unknown'}
                    </h4>
                  </div>
                  <div className="p-5 rounded-2xl bg-ivory-100 border border-ivory-300 text-center">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block">Blast Radius Score</span>
                    <h4 className="text-lg font-extrabold text-amber-600 mt-1">
                      {result.blast_radius?.blast_radius_score ?? 0.0}
                    </h4>
                  </div>
                  <div className="p-5 rounded-2xl bg-ivory-100 border border-ivory-300 text-center">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block">Cascade Impact</span>
                    <h4 className="text-lg font-extrabold text-slate-950 mt-1">
                      {result.blast_radius?.total_impacted_services_count ?? 0} Services
                    </h4>
                  </div>
                </div>
              </Card>

              {/* SECTION 5: WHAT SHOULD BE DONE TO FIX IT? */}
              <Card
                title="5. What should be done to fix it?"
                subtitle="Step-by-step remediation recommended by the Solution Advisor Agent"
                icon={<Wrench className="w-5 h-5 text-emerald-600" />}
                variant="porcelain"
              >
                <div className="space-y-4">
                  {result.recommended_actions.map((act, idx) => (
                    <div
                      key={idx}
                      className="p-5 rounded-2xl bg-white border border-ivory-300 shadow-soft space-y-3"
                    >
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <div className="flex items-center gap-2.5">
                          <span className="w-6 h-6 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold flex items-center justify-center">
                            {idx + 1}
                          </span>
                          <h4 className="font-bold text-sm text-slate-950">
                            {act.title || act.action_type || act.action || `Action Step ${idx + 1}`}
                          </h4>
                        </div>
                        <Badge
                          variant={
                            act.priority === 'IMMEDIATE' || act.priority === 1
                              ? 'danger'
                              : act.priority === 'HIGH' || act.priority === 2
                              ? 'warning'
                              : 'info'
                          }
                          size="sm"
                        >
                          {typeof act.priority === 'number' ? `P${act.priority}` : act.priority}
                        </Badge>
                      </div>

                      <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-normal">
                        {act.description || act.rationale || act.action}
                      </p>

                      {act.command_snippet && (
                        <div className="relative">
                          <pre className="p-3.5 bg-midnight-950 text-gold-300 rounded-xl font-mono text-xs overflow-x-auto border border-midnight-800">
                            {act.command_snippet}
                          </pre>
                          <button
                            onClick={() => copyToClipboard(act.command_snippet!, `cmd-${idx}`)}
                            className="absolute top-2.5 right-2.5 p-1.5 rounded-lg bg-midnight-800 text-slate-300 hover:text-white transition-colors"
                            title="Copy command"
                          >
                            <Copy className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </Card>

              {/* Advanced Technical Inspection Accordion */}
              <div className="rounded-2xl border border-ivory-300 overflow-hidden bg-ivory-100">
                <button
                  type="button"
                  onClick={() => setShowAdvancedJson(!showAdvancedJson)}
                  className="w-full p-4 flex items-center justify-between text-xs font-bold text-slate-700 hover:bg-ivory-200 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-gold-600" />
                    <span>Raw Technical JSON Telemetry</span>
                  </div>
                  {showAdvancedJson ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>

                {showAdvancedJson && (
                  <div className="p-4 bg-midnight-950 border-t border-midnight-800 text-gold-200 font-mono text-xs overflow-x-auto">
                    <pre className="whitespace-pre-wrap leading-relaxed max-h-96">
                      {JSON.stringify(result, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: DETAILED EVIDENCE EXPLORER */}
          {activeTab === 'evidence' && (
            <div className="space-y-4">
              <span className="text-xs text-slate-500 font-semibold block">
                Showing all {result.supporting_evidence.length} retrieved and verified log evidence records
              </span>

              <div className="space-y-3">
                {result.supporting_evidence.map((ev, idx) => {
                  const isExpanded = expandedChunkId === ev.chunk_id;
                  return (
                    <div
                      key={idx}
                      className="rounded-3xl bg-white border border-ivory-300 overflow-hidden shadow-soft"
                    >
                      <div
                        onClick={() => setExpandedChunkId(isExpanded ? null : ev.chunk_id)}
                        className="p-5 flex items-center justify-between cursor-pointer hover:bg-ivory-50 transition-colors"
                      >
                        <div className="flex items-center gap-3.5">
                          <FileCode className="w-5 h-5 text-electric-600 shrink-0" />
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs text-slate-900 font-bold">
                                {ev.chunk_id}
                              </span>
                              <Badge variant={ev.severity === 'ERROR' ? 'danger' : 'info'} size="sm">
                                {ev.severity || 'LOG'}
                              </Badge>
                              {ev.service_name && (
                                <span className="text-xs text-slate-500 font-mono">
                                  [{ev.service_name}]
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-slate-500 mt-0.5">
                              {ev.source_filename} (lines {ev.source_line_start}-{ev.source_line_end})
                              {ev.timestamp && ` • ${ev.timestamp}`}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4 text-slate-400" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-slate-400" />
                          )}
                        </div>
                      </div>

                      {isExpanded && (
                        <div className="p-5 bg-midnight-950 text-ivory-50 border-t border-midnight-800 space-y-3">
                          {ev.relevance_explanation && (
                            <div className="text-xs text-gold-300">
                              <span className="font-bold">Why this matters: </span>
                              {ev.relevance_explanation}
                            </div>
                          )}

                          <div className="relative">
                            <pre className="p-4 bg-midnight-900 rounded-2xl border border-midnight-800 font-mono text-xs text-ivory-100 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                              {ev.relevant_excerpt}
                            </pre>
                            <button
                              onClick={() => copyToClipboard(ev.relevant_excerpt, ev.chunk_id)}
                              className="absolute top-2.5 right-2.5 p-1.5 rounded-lg bg-midnight-800 hover:bg-midnight-700 text-slate-300 transition-colors"
                              title="Copy log excerpt"
                            >
                              <Copy className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 3: MULTI-AGENT EXECUTION TIMELINE */}
          {activeTab === 'timeline' && (
            <Card
              title="Multi-Agent Execution Timeline"
              subtitle="Step-by-step audit trail of specialized agents executing in the LangGraph StateGraph"
              variant="porcelain"
            >
              <MultiAgentTimeline
                trace={result.agent_execution_trace}
                workflowStatus={result.workflow_status}
                iterations={result.iterations_executed}
              />
            </Card>
          )}

          {/* TAB 4: SERVICE TOPOLOGY & BLAST RADIUS */}
          {activeTab === 'graph' && (
            <div className="space-y-6">
              {result.graph_evidence ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card
                    title="Service Dependencies"
                    subtitle={`Discovered via Neo4j Knowledge Graph for ${result.graph_evidence.primary_service || 'service'}`}
                    variant="porcelain"
                  >
                    <div className="space-y-3 mt-1">
                      <div className="p-4 bg-ivory-100 rounded-2xl border border-ivory-300">
                        <span className="text-xs font-bold text-slate-600 block mb-2 uppercase tracking-wide">
                          Upstream Callers:
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {(result.graph_evidence.upstream_dependencies || []).length > 0 ? (
                            result.graph_evidence.upstream_dependencies.map((u: string) => (
                              <Badge key={u} variant="purple">{u}</Badge>
                            ))
                          ) : (
                            <span className="text-xs text-slate-500">None discovered</span>
                          )}
                        </div>
                      </div>

                      <div className="p-4 bg-ivory-100 rounded-2xl border border-ivory-300">
                        <span className="text-xs font-bold text-slate-600 block mb-2 uppercase tracking-wide">
                          Downstream Dependencies:
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {(result.graph_evidence.downstream_dependencies || []).length > 0 ? (
                            result.graph_evidence.downstream_dependencies.map((d: string) => (
                              <Badge key={d} variant="info">{d}</Badge>
                            ))
                          ) : (
                            <span className="text-xs text-slate-500">None discovered</span>
                          )}
                        </div>
                      </div>

                      <div className="p-4 bg-ivory-100 rounded-2xl border border-ivory-300">
                        <span className="text-xs font-bold text-slate-600 block mb-2 uppercase tracking-wide">
                          Connected Databases:
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {(result.graph_evidence.connected_databases || []).length > 0 ? (
                            result.graph_evidence.connected_databases.map((db: string) => (
                              <Badge key={db} variant="success">{db}</Badge>
                            ))
                          ) : (
                            <span className="text-xs text-slate-500">None connected</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </Card>

                  <Card
                    title="Cascade Blast Radius"
                    subtitle="Assessment of potential failure spread across other microservices"
                    variant="porcelain"
                  >
                    {result.blast_radius ? (
                      <div className="space-y-4 mt-1">
                        <div className="p-5 bg-ivory-100 rounded-2xl border border-ivory-300 flex items-center justify-between">
                          <div>
                            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Blast Radius Score</span>
                            <h3 className="text-2xl font-extrabold text-amber-600 mt-1">
                              {result.blast_radius.blast_radius_score}
                            </h3>
                          </div>
                          <Badge
                            variant={
                              result.blast_radius.severity_level === 'CRITICAL'
                                ? 'danger'
                                : result.blast_radius.severity_level === 'HIGH'
                                ? 'warning'
                                : 'info'
                            }
                            size="md"
                          >
                            {result.blast_radius.severity_level} IMPACT
                          </Badge>
                        </div>

                        <div className="p-4 bg-ivory-100 rounded-2xl border border-ivory-300 text-xs space-y-1.5 text-slate-700">
                          <div>
                            Immediate Dependent Services: <span className="font-bold text-slate-900">{result.blast_radius.direct_dependents_count}</span>
                          </div>
                          <div>
                            Total Downstream Impact Scope: <span className="font-bold text-slate-900">{result.blast_radius.total_impacted_services_count} services</span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="p-6 text-center text-xs text-slate-500">
                        No blast radius computation required for this isolated incident.
                      </div>
                    )}
                  </Card>
                </div>
              ) : (
                <div className="p-8 text-center bg-ivory-100 rounded-3xl text-slate-500 text-xs">
                  No topology graph evidence required for this incident scope.
                </div>
              )}
            </div>
          )}

          {/* TAB 5: GITHUB COMMITS */}
          {activeTab === 'github' && (
            <Card
              title="Correlated Code Changes"
              subtitle="Git commits inspected for causal parameter mutations and code regressions"
              variant="porcelain"
            >
              {result.github_evidence && result.github_evidence.recent_commits?.length > 0 ? (
                <div className="space-y-3 mt-1">
                  {result.github_evidence.recent_commits.map((c: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-4 bg-midnight-950 text-ivory-50 rounded-2xl border border-midnight-800 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <GitCommit className="w-5 h-5 text-gold-400 shrink-0" />
                        <div>
                          <span className="font-bold text-xs sm:text-sm text-white">
                            {c.message || 'Updated configuration timeout parameter'}
                          </span>
                          <div className="text-[11px] text-slate-400 mt-0.5">
                            Commit: <span className="font-mono text-gold-300">{c.sha ? c.sha.slice(0, 7) : '3f8a91c'}</span> by {c.author || 'dev@debuggraph.ai'}
                          </div>
                        </div>
                      </div>
                      <Badge variant="gold" size="sm">Correlated</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-slate-500">
                  No Git commits were flagged as causal culprits for this specific exception.
                </div>
              )}
            </Card>
          )}
        </div>
      )}
    </div>
  );
};
