import React from 'react';
import { AgentExecutionStep } from '../../types';
import {
  AlertCircle,
  Bot,
  CheckCircle2,
  Clock,
  Compass,
  FileSearch,
  GitCommit,
  Network,
  ShieldAlert,
  Sparkles,
  Wrench,
  Radio,
} from 'lucide-react';
import { Badge } from '../ui/Badge';

interface MultiAgentTimelineProps {
  trace?: AgentExecutionStep[];
  workflowStatus?: string;
  iterations?: number;
}

export const MultiAgentTimeline: React.FC<MultiAgentTimelineProps> = ({
  trace = [],
  workflowStatus = 'SUCCESS',
  iterations = 1,
}) => {
  const agentConfig: Record<
    string,
    { title: string; role: string; icon: React.ReactNode; badgeVariant: 'gold' | 'info' | 'success' | 'accent' | 'warning' | 'danger' | 'default' }
  > = {
    SupervisorAgent: {
      title: 'Supervisor Agent',
      role: 'Workflow Coordinator',
      icon: <Compass className="w-4 h-4 text-gold-600" />,
      badgeVariant: 'gold',
    },
    LogInvestigatorAgent: {
      title: 'Log Detective Agent',
      role: 'Log Retrieval & Hybrid Search',
      icon: <FileSearch className="w-4 h-4 text-electric-600" />,
      badgeVariant: 'info',
    },
    GraphInvestigatorAgent: {
      title: 'Topology Specialist',
      role: 'Service Dependency & Blast Radius',
      icon: <Network className="w-4 h-4 text-emerald-600" />,
      badgeVariant: 'success',
    },
    GitHubInvestigatorAgent: {
      title: 'Code Inspector Agent',
      role: 'Git Commit & Diff Correlation',
      icon: <GitCommit className="w-4 h-4 text-violet-600" />,
      badgeVariant: 'accent',
    },
    RootCauseAnalystAgent: {
      title: 'Root Cause Analyst',
      role: 'Hypothesis Generation & Reasoning',
      icon: <Sparkles className="w-4 h-4 text-amber-600" />,
      badgeVariant: 'warning',
    },
    EvidenceValidatorAgent: {
      title: 'Evidence Validator',
      role: 'Citation Grounding & Anti-Hallucination Gate',
      icon: <ShieldAlert className="w-4 h-4 text-rose-600" />,
      badgeVariant: 'danger',
    },
    ResolutionAdvisorAgent: {
      title: 'Resolution Advisor',
      role: 'Remediation Steps & Safety Verification',
      icon: <Wrench className="w-4 h-4 text-electric-600" />,
      badgeVariant: 'info',
    },
  };

  if (!trace || trace.length === 0) {
    return (
      <div className="p-8 text-center bg-ivory-100 border border-ivory-300 rounded-3xl">
        <Bot className="w-8 h-8 text-slate-400 mx-auto mb-2" />
        <h4 className="text-sm font-bold text-slate-800">Single-Pass Investigation</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto leading-relaxed">
          This investigation was executed using the direct fast-path model without triggering the multi-agent orchestration loop.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Overview Horological Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-gradient-to-r from-ivory-100 via-white to-ivory-100 border border-ivory-300 rounded-3xl shadow-soft">
        <div className="flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-2xl bg-white border border-gold-300 shadow-glow-gold flex items-center justify-center shrink-0">
            <CheckCircle2 className="w-5 h-5 text-gold-600" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm sm:text-base font-extrabold text-slate-950">
                Multi-Agent Orchestration Trace
              </h4>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-electric-50 text-electric-700 border border-electric-200">
                LangGraph StateGraph
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-0.5">
              {trace.length} specialized agent steps orchestrated across {iterations} reasoning pass{iterations > 1 ? 'es' : ''} with anti-hallucination verification
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Badge
            variant={
              workflowStatus === 'SUCCESS'
                ? 'success'
                : workflowStatus === 'INSUFFICIENT_EVIDENCE'
                ? 'warning'
                : 'info'
            }
            dot
            size="md"
          >
            {workflowStatus === 'SUCCESS' ? '100% Consensus Verified' : workflowStatus}
          </Badge>
        </div>
      </div>

      {/* Stepper Timeline with Gold/Electric Rails */}
      <div className="relative pl-8 space-y-4 before:absolute before:left-3.5 before:top-4 before:bottom-4 before:w-[2px] before:bg-gradient-to-b before:from-gold-400 before:via-electric-400 before:to-emerald-400">
        {trace.map((step, idx) => {
          const config = agentConfig[step.agent_name] || {
            title: step.agent_name,
            role: step.stage,
            icon: <Bot className="w-4 h-4 text-electric-600" />,
            badgeVariant: 'default' as const,
          };

          return (
            <div key={idx} className="relative group animate-fade-in">
              {/* Complication Avatar */}
              <div className="absolute -left-[38px] top-2 w-8 h-8 rounded-2xl bg-white border border-ivory-300 shadow-soft flex items-center justify-center shrink-0 group-hover:scale-110 group-hover:border-gold-400 transition-all">
                {config.icon}
              </div>

              {/* Step Card with Tactile Feel */}
              <div className="bg-white border border-ivory-300 hover:border-gold-300 rounded-3xl p-5 shadow-card hover:shadow-card-hover transition-all">
                <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                  <div className="flex items-center gap-2.5">
                    <span className="font-extrabold text-xs sm:text-sm text-slate-950">
                      {config.title}
                    </span>
                    <span className="text-[11px] text-slate-500 font-medium">
                      ({config.role})
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {step.latency_ms !== undefined && step.latency_ms !== null && (
                      <span className="text-[11px] font-mono text-slate-600 flex items-center gap-1 bg-ivory-100 px-2 py-0.5 rounded-lg border border-ivory-300">
                        <Clock className="w-3 h-3 text-gold-600" />
                        {step.latency_ms.toFixed(0)} ms
                      </span>
                    )}
                    <Badge
                      variant={
                        step.status === 'COMPLETED'
                          ? 'success'
                          : step.status === 'SKIPPED'
                          ? 'secondary'
                          : 'danger'
                      }
                      size="sm"
                    >
                      {step.status === 'COMPLETED' ? 'Completed' : step.status}
                    </Badge>
                  </div>
                </div>

                <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-normal">
                  {step.summary}
                </p>

                {/* Micro Stage Telemetry */}
                <div className="mt-3 pt-2.5 border-t border-ivory-200 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                  <span>Stage: {step.stage}</span>
                  <span>{new Date(step.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
