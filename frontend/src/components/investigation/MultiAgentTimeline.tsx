import React from 'react';
import { AgentExecutionStep } from '../../types';
import {
  CheckCircle2,
  Clock,
  Compass,
  FileSearch,
  GitCommit,
  Network,
  ShieldAlert,
  Sparkles,
  Wrench,
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
  const agentIcons: Record<string, React.ReactNode> = {
    SupervisorAgent: <Compass className="w-4 h-4 text-indigo-400" />,
    LogInvestigatorAgent: <FileSearch className="w-4 h-4 text-cyan-400" />,
    GraphInvestigatorAgent: <Network className="w-4 h-4 text-emerald-400" />,
    GitHubInvestigatorAgent: <GitCommit className="w-4 h-4 text-violet-400" />,
    RootCauseAnalystAgent: <Sparkles className="w-4 h-4 text-amber-400" />,
    EvidenceValidatorAgent: <ShieldAlert className="w-4 h-4 text-rose-400" />,
    ResolutionAdvisorAgent: <Wrench className="w-4 h-4 text-blue-400" />,
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <Badge variant="success" size="sm">COMPLETED</Badge>;
      case 'SKIPPED':
        return <Badge variant="warning" size="sm">SKIPPED</Badge>;
      case 'FAILED':
        return <Badge variant="danger" size="sm">FAILED</Badge>;
      default:
        return <Badge variant="default" size="sm">{status}</Badge>;
    }
  };

  if (!trace || trace.length === 0) {
    return (
      <div className="p-6 text-center text-slate-500 font-mono text-xs">
        No multi-agent trace available for this single-pass investigation.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Overview Banner */}
      <div className="flex items-center justify-between p-3.5 bg-slate-900/60 border border-slate-800 rounded-lg">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-200">
              LangGraph StateGraph Workflow Orchestrated
            </h4>
            <p className="text-[11px] text-slate-400 font-mono">
              Executed {trace.length} agent steps across {iterations} iteration(s)
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant={
              workflowStatus === 'SUCCESS'
                ? 'success'
                : workflowStatus === 'INSUFFICIENT_EVIDENCE'
                ? 'warning'
                : 'info'
            }
          >
            {workflowStatus}
          </Badge>
        </div>
      </div>

      {/* Timeline List */}
      <div className="relative pl-6 space-y-4 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {trace.map((step, idx) => {
          const icon = agentIcons[step.agent_name] || <Clock className="w-4 h-4 text-slate-400" />;
          return (
            <div key={idx} className="relative group">
              {/* Bullet circle */}
              <div className="absolute -left-[27px] top-1 w-6 h-6 rounded-full bg-dark-900 border border-slate-700 flex items-center justify-center shadow-sm">
                {icon}
              </div>

              {/* Step Card */}
              <div className="bg-slate-900/80 border border-slate-800/90 hover:border-slate-700/90 rounded-lg p-3.5 transition-colors">
                <div className="flex items-center justify-between mb-1.5 flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-xs text-white">
                      {step.agent_name}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400">
                      [{step.stage}]
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {step.latency_ms !== undefined && step.latency_ms !== null && (
                      <span className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {step.latency_ms.toFixed(1)}ms
                      </span>
                    )}
                    {getStatusBadge(step.status)}
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  {step.summary}
                </p>

                <div className="mt-2 text-[10px] text-slate-400 font-mono">
                  {new Date(step.timestamp).toLocaleTimeString()} UTC
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

