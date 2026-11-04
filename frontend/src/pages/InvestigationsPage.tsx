import React, { useState } from 'react';
import {
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
  const [activeTab, setActiveTab] = useState<'summary' | 'evidence' | 'timeline' | 'graph' | 'github'>('summary');
  const [expandedChunkId, setExpandedChunkId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

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
      setActiveTab('summary');
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
    if (s === 'CRITICAL') return <Badge variant="danger">CRITICAL</Badge>;
    if (s === 'HIGH') return <Badge variant="danger">HIGH</Badge>;
    if (s === 'MEDIUM' || s === 'WARN') return <Badge variant="warning">MEDIUM</Badge>;
    return <Badge variant="info">{sev || 'UNKNOWN'}</Badge>;
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Investigation Request Form */}
      <Card
        title="Incident Investigation Request"
        subtitle="Submit natural language symptom queries to activate the hybrid retrieval and LangGraph multi-agent pipeline"
      >
        <form onSubmit={handleInvestigate} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 font-mono mb-1.5">
              Incident Symptom Query or Exception Description *
            </label>
            <div className="relative">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={3}
                placeholder="e.g. Why is payment-service failing with ConnectionTimeoutError during Stripe checkout?"
                className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono resize-none transition-colors"
                required
              />
              <div className="absolute right-3 bottom-3 flex items-center gap-2">
                <span className="text-[10px] text-slate-400 font-mono">
                  {query.length} chars
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Investigation Mode */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 font-mono mb-1.5">
                Investigation Mode
              </label>
              <div className="grid grid-cols-2 gap-2 p-1 bg-slate-950 border border-slate-800 rounded-lg">
                <button
                  type="button"
                  onClick={() => setInvestigationMode('agentic')}
                  className={`py-1.5 text-xs font-mono rounded-md transition-all flex items-center justify-center gap-1.5 ${
                    investigationMode === 'agentic'
                      ? 'bg-gradient-to-r from-indigo-600 to-cyan-600 text-white font-bold shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Bot className="w-3.5 h-3.5" />
                  <span>7 Agents</span>
                </button>
                <button
                  type="button"
                  onClick={() => setInvestigationMode('standard')}
                  className={`py-1.5 text-xs font-mono rounded-md transition-all flex items-center justify-center gap-1.5 ${
                    investigationMode === 'standard'
                      ? 'bg-slate-800 text-cyan-300 font-bold border border-slate-700'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Zap className="w-3.5 h-3.5" />
                  <span>Single-Pass</span>
                </button>
              </div>
            </div>

            {/* Service Name Filter */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 font-mono mb-1.5">
                Target Microservice (Optional)
              </label>
              <input
                type="text"
                value={serviceName}
                onChange={(e) => setServiceName(e.target.value)}
                placeholder="e.g. payment-service"
                className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>

            {/* Severity Filter */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 font-mono mb-1.5">
                Severity Filter
              </label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value="">Any Severity</option>
                <option value="CRITICAL">CRITICAL</option>
                <option value="ERROR">ERROR</option>
                <option value="WARN">WARN / WARNING</option>
                <option value="INFO">INFO</option>
              </select>
            </div>

            {/* Top K */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 font-mono mb-1.5">
                Retrieval Candidates ({topK} chunks)
              </label>
              <input
                type="range"
                min="3"
                max="30"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer h-2 bg-slate-800 rounded-lg mt-3"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 flex-wrap gap-3">
            <div className="text-[11px] text-slate-400 font-mono flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>EvidenceValidator enforces 0% hallucinated citations</span>
            </div>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 font-mono disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Orchestrating 7 Agents...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Execute Multi-Agent RCA</span>
                </>
              )}
            </button>
          </div>
        </form>
      </Card>

      {/* Loading Indicator */}
      {loading && (
        <Card className="text-center py-12">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center mx-auto mb-4 animate-pulse">
            <Sparkles className="w-8 h-8 text-cyan-400 animate-spin" />
          </div>
          <h3 className="text-base font-bold text-white">
            Investigating Incident with 7 LangGraph Agents
          </h3>
          <p className="text-xs text-slate-400 font-mono mt-1 max-w-md mx-auto">
            1. Hybrid Retrieval &rarr; 2. Neo4j Topology &rarr; 3. GitHub Commits &rarr; 4. Root Cause Synthesis &rarr; 5. Grounding Gate
          </p>
        </Card>
      )}

      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800 rounded-xl flex items-start gap-3">
          <AlertOctagon className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-xs font-bold text-rose-300 font-mono">Investigation Error</h4>
            <p className="text-xs text-rose-200 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Investigation Results View */}
      {result && !loading && (
        <div className="space-y-6">
          {/* Header Summary Banner */}
          <div className="p-5 bg-gradient-to-r from-dark-900 to-slate-900 border border-slate-800 rounded-2xl shadow-xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-slate-400">
                    ID: {result.investigation_id}
                  </span>
                  {getSeverityBadge(result.severity_assessment)}
                  <Badge variant="purple">
                    {result.workflow_status || 'SUCCESS'}
                  </Badge>
                  <span className="text-xs font-mono text-slate-400">
                    {new Date(result.created_at).toLocaleTimeString()} UTC
                  </span>
                </div>
                <h2 className="text-lg font-bold text-white tracking-tight">
                  {result.incident_summary}
                </h2>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => copyToClipboard(JSON.stringify(result, null, 2), 'raw_json')}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs font-mono transition-colors flex items-center gap-1.5"
                >
                  <Copy className="w-3.5 h-3.5" />
                  <span>{copiedId === 'raw_json' ? 'Copied!' : 'Copy JSON'}</span>
                </button>
              </div>
            </div>

            {/* Sub-bar metrics */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 pt-1">
              <div>
                <span className="text-[11px] font-mono text-slate-400">Affected Services</span>
                <p className="text-sm font-bold text-slate-200 font-mono mt-0.5">
                  {result.affected_services.join(', ') || 'N/A'}
                </p>
              </div>
              <div>
                <span className="text-[11px] font-mono text-slate-400">Evidence Chunks</span>
                <p className="text-sm font-bold text-cyan-400 font-mono mt-0.5">
                  {result.retrieved_chunks_count} retrieved chunks
                </p>
              </div>
              <div>
                <span className="text-[11px] font-mono text-slate-400">Evidence Sufficiency</span>
                <p className="text-sm font-bold text-emerald-400 font-mono mt-0.5">
                  {result.evidence_sufficiency.status} ({(result.evidence_sufficiency.confidence_score * 100).toFixed(0)}%)
                </p>
              </div>
              <div>
                <span className="text-[11px] font-mono text-slate-400">Reasoning Agent</span>
                <p className="text-sm font-bold text-indigo-400 font-mono mt-0.5 truncate" title={result.model_information.model_name}>
                  {result.model_information.model_name}
                </p>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
            {[
              { id: 'summary' as const, label: 'Root Cause & Recommendations', icon: Sparkles },
              { id: 'evidence' as const, label: `Evidence Explorer (${result.supporting_evidence.length})`, icon: FileText },
              { id: 'timeline' as const, label: `7-Agent Trace (${result.agent_execution_trace?.length || 0})`, icon: Bot },
              { id: 'graph' as const, label: 'Service Topology & Blast Radius', icon: Network },
              { id: 'github' as const, label: 'GitHub Commit Intelligence', icon: GitCommit },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-mono font-medium transition-all ${
                    isActive
                      ? 'bg-indigo-600/20 text-cyan-300 border border-indigo-500/40'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* TAB 1: ROOT CAUSE & RECOMMENDATIONS */}
          {activeTab === 'summary' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column: Root Cause Hypotheses */}
              <div className="lg:col-span-2 space-y-6">
                <Card
                  title="Ranked Root Cause Hypotheses"
                  subtitle="Evidence-grounded explanations validated against retrieved log chunks"
                >
                  <div className="space-y-4 mt-2">
                    {result.potential_root_causes.map((rc, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-colors"
                      >
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-cyan-300 border border-indigo-500/40 text-xs font-mono flex items-center justify-center font-bold">
                              {rc.rank}
                            </span>
                            <h4 className="font-bold text-sm text-white">
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
                            size="sm"
                          >
                            {rc.confidence} Confidence
                          </Badge>
                        </div>

                        <p className="text-xs text-slate-300 leading-relaxed font-sans mb-3">
                          {rc.reasoning}
                        </p>

                        {rc.confidence_reasoning && (
                          <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/80 text-[11px] text-slate-400 font-mono mb-3">
                            <span className="text-slate-300 font-semibold">Validation Rationale: </span>
                            {rc.confidence_reasoning}
                          </div>
                        )}

                        {rc.supporting_evidence_ids.length > 0 && (
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-[10px] text-slate-400 font-mono">
                              Cited Ground-Truth Chunks:
                            </span>
                            {rc.supporting_evidence_ids.map((cid) => (
                              <button
                                key={cid}
                                onClick={() => {
                                  setActiveTab('evidence');
                                  setExpandedChunkId(cid);
                                }}
                                className="px-2 py-0.5 rounded bg-indigo-950/60 text-cyan-400 border border-indigo-800/60 text-[10px] font-mono hover:bg-indigo-900/60 transition-colors"
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

                {/* Key Observations */}
                <Card
                  title="Observable Facts & Anomalies"
                  subtitle="Explicit events observed directly in log evidence vs hypothesized deductions"
                >
                  <div className="space-y-2.5 mt-2">
                    {result.key_observations.map((obs, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-slate-900/60 rounded-lg border border-slate-800/80 flex items-start justify-between gap-3"
                      >
                        <div className="flex items-start gap-2.5">
                          <div className="mt-0.5">
                            {obs.is_fact ? (
                              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                            ) : (
                              <Info className="w-4 h-4 text-amber-400" />
                            )}
                          </div>
                          <div>
                            <p className="text-xs text-slate-200 leading-relaxed">
                              {obs.observation}
                            </p>
                            <div className="flex items-center gap-2 mt-1.5 text-[10px] font-mono text-slate-400">
                              {obs.affected_service && (
                                <span className="text-slate-300">[{obs.affected_service}]</span>
                              )}
                              {obs.timestamp && <span>{obs.timestamp}</span>}
                            </div>
                          </div>
                        </div>

                        <Badge variant={obs.is_fact ? 'success' : 'warning'} size="sm">
                          {obs.is_fact ? 'FACT' : 'INFERENCE'}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              {/* Right Column: Prioritized Remediation */}
              <div className="space-y-6">
                <Card
                  title="Prioritized Remediation Actions"
                  subtitle="Generated by Resolution Advisor Agent with safety boundaries"
                >
                  <div className="space-y-3 mt-2">
                    {result.recommended_actions.map((act, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 bg-slate-900/80 rounded-xl border border-slate-800"
                      >
                        <div className="flex items-center justify-between gap-2 mb-1.5">
                          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                            Priority #{act.priority}
                          </span>
                          <Badge variant="info" size="sm">
                            {act.category}
                          </Badge>
                        </div>
                        <h5 className="font-semibold text-xs text-slate-100">
                          {act.action}
                        </h5>
                        <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                          {act.rationale}
                        </p>
                        {act.safety_warning && (
                          <div className="mt-2.5 p-2 bg-rose-950/40 border border-rose-800/80 rounded-lg flex items-start gap-2 text-[10px] text-rose-300 font-mono">
                            <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
                            <span>Caution: {act.safety_warning}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>

                {/* Further Investigation */}
                <Card title="Diagnostic Next Steps" subtitle="Telemetry and healthchecks to verify">
                  <div className="space-y-3 mt-2">
                    <div>
                      <span className="text-[11px] font-mono text-slate-400 block mb-1">
                        Recommended Commands:
                      </span>
                      <div className="space-y-1.5">
                        {result.further_investigation.recommended_checks.map((check, idx) => (
                          <div
                            key={idx}
                            className="p-2 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs text-cyan-300 flex items-center justify-between"
                          >
                            <span className="truncate">{check}</span>
                            <button
                              onClick={() => copyToClipboard(check, `check_${idx}`)}
                              className="text-slate-500 hover:text-slate-300"
                            >
                              <Copy className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          )}

          {/* TAB 2: EVIDENCE EXPLORER */}
          {activeTab === 'evidence' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-slate-400">
                  Showing {result.supporting_evidence.length} verified log evidence records
                </span>
              </div>

              <div className="space-y-3">
                {result.supporting_evidence.map((ev, idx) => {
                  const isExpanded = expandedChunkId === ev.chunk_id;
                  return (
                    <div
                      key={idx}
                      className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden"
                    >
                      <div
                        onClick={() => setExpandedChunkId(isExpanded ? null : ev.chunk_id)}
                        className="p-3.5 flex items-center justify-between cursor-pointer hover:bg-slate-850 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <FileCode className="w-4 h-4 text-cyan-400 shrink-0" />
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs text-white font-bold">
                                {ev.chunk_id}
                              </span>
                              <Badge variant={ev.severity === 'ERROR' ? 'danger' : 'info'} size="sm">
                                {ev.severity || 'LOG'}
                              </Badge>
                              {ev.service_name && (
                                <span className="text-[11px] font-mono text-slate-400">
                                  [{ev.service_name}]
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] font-mono text-slate-400 mt-0.5">
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
                        <div className="p-4 bg-slate-950 border-t border-slate-800 space-y-3">
                          {ev.relevance_explanation && (
                            <div className="text-xs text-slate-300 font-sans">
                              <span className="font-semibold text-cyan-300 font-mono">Relevance: </span>
                              {ev.relevance_explanation}
                            </div>
                          )}

                          <div className="relative">
                            <pre className="p-3.5 bg-dark-950 rounded-lg border border-slate-800 font-mono text-xs text-slate-200 overflow-x-auto whitespace-pre-wrap leading-relaxed selection:bg-cyan-500 selection:text-black">
                              {ev.relevant_excerpt}
                            </pre>
                            <button
                              onClick={() => copyToClipboard(ev.relevant_excerpt, ev.chunk_id)}
                              className="absolute top-2 right-2 p-1.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
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
              title="LangGraph 7-Agent Execution Trace"
              subtitle="Step-by-step audit log of agent interactions, decisions, and execution latencies"
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
                    title="Service Neighborhood & Dependencies"
                    subtitle={`Discovered via Neo4j Knowledge Graph for ${result.graph_evidence.primary_service || 'service'}`}
                  >
                    <div className="space-y-3 mt-2">
                      <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                        <span className="text-[11px] font-mono text-slate-400 block mb-1">
                          Upstream Callers (Dependents):
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {(result.graph_evidence.upstream_dependencies || []).length > 0 ? (
                            result.graph_evidence.upstream_dependencies.map((u: string) => (
                              <Badge key={u} variant="purple">{u}</Badge>
                            ))
                          ) : (
                            <span className="text-xs text-slate-500 font-mono">None discovered</span>
                          )}
                        </div>
                      </div>

                      <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                        <span className="text-[11px] font-mono text-slate-400 block mb-1">
                          Downstream Callees (Dependencies):
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {(result.graph_evidence.downstream_dependencies || []).length > 0 ? (
                            result.graph_evidence.downstream_dependencies.map((d: string) => (
                              <Badge key={d} variant="info">{d}</Badge>
                            ))
                          ) : (
                            <span className="text-xs text-slate-500 font-mono">None discovered</span>
                          )}
                        </div>
                      </div>

                      <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                        <span className="text-[11px] font-mono text-slate-400 block mb-1">
                          Connected Databases & Storage:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {(result.graph_evidence.connected_databases || []).length > 0 ? (
                            result.graph_evidence.connected_databases.map((db: string) => (
                              <Badge key={db} variant="success">{db}</Badge>
                            ))
                          ) : (
                            <span className="text-xs text-slate-500 font-mono">None connected</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </Card>

                  <Card
                    title="Failure Blast Radius Calculation"
                    subtitle="Assessed cascade risk and failure propagation"
                  >
                    {result.blast_radius ? (
                      <div className="space-y-4 mt-2">
                        <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
                          <div>
                            <span className="text-xs font-mono text-slate-400">Blast Radius Score</span>
                            <h3 className="text-2xl font-extrabold text-cyan-400 mt-0.5">
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
                          >
                            {result.blast_radius.severity_level} IMPACT
                          </Badge>
                        </div>

                        <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs font-mono space-y-1">
                          <div className="text-slate-400">
                            Immediate Dependents: <span className="text-white font-bold">{result.blast_radius.direct_dependents_count}</span>
                          </div>
                          <div className="text-slate-400">
                            Total Cascade Scope: <span className="text-white font-bold">{result.blast_radius.total_impacted_services_count} services</span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 font-mono py-6 text-center">
                        Blast radius calculation skipped or not applicable.
                      </p>
                    )}
                  </Card>
                </div>
              ) : (
                <Card className="text-center py-8">
                  <Network className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                  <p className="text-xs text-slate-400 font-mono">
                    No graph topology evidence available for this incident inquiry.
                  </p>
                </Card>
              )}
            </div>
          )}

          {/* TAB 5: GITHUB COMMIT INTELLIGENCE */}
          {activeTab === 'github' && (
            <div className="space-y-4">
              {result.github_evidence && result.github_evidence.candidate_commits ? (
                <Card
                  title={`Correlated Commits in ${result.github_evidence.repository || 'Repository'}`}
                  subtitle={result.github_evidence.analysis_summary}
                >
                  <div className="space-y-3 mt-3">
                    {result.github_evidence.candidate_commits.map((c: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2"
                      >
                        <div className="flex items-center justify-between gap-2 flex-wrap">
                          <div className="flex items-center gap-2">
                            <GitCommit className="w-4 h-4 text-violet-400" />
                            <span className="font-mono text-xs font-bold text-white">
                              {c.short_sha}
                            </span>
                            <span className="text-xs text-slate-400">by {c.author}</span>
                          </div>
                          <Badge variant="purple" size="sm">
                            {(c.relevance_score * 100).toFixed(0)}% Match
                          </Badge>
                        </div>

                        <p className="text-xs text-slate-300">
                          {c.correlation_reasoning}
                        </p>

                        {c.diff_excerpt && (
                          <pre className="p-3 bg-dark-950 rounded-lg border border-slate-800 text-[11px] font-mono text-cyan-300 overflow-x-auto whitespace-pre-wrap">
                            {c.diff_excerpt}
                          </pre>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              ) : (
                <Card className="text-center py-8">
                  <GitCommit className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                  <p className="text-xs text-slate-400 font-mono">
                    No suspect GitHub commits detected matching the reported error signatures.
                  </p>
                </Card>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

