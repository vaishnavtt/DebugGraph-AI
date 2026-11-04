import React from 'react';
import { NavTab } from './Sidebar';
import { Activity, Bell, ExternalLink, RefreshCw, Terminal } from 'lucide-react';
import { Badge } from '../ui/Badge';

interface HeaderProps {
  activeTab: NavTab;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  onQuickInvestigate?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onRefresh,
  isRefreshing = false,
  onQuickInvestigate,
}) => {
  const titles: Record<NavTab, { title: string; subtitle: string }> = {
    overview: {
      title: 'Operations Dashboard',
      subtitle: 'Real-time telemetry, knowledge graph status, and incident pipeline',
    },
    investigations: {
      title: 'Incident Investigation Workspace',
      subtitle: 'Multi-agent RCA powered by LangGraph, Gemini, and Hybrid Retrieval',
    },
    logs: {
      title: 'Log Ingestion & Hybrid Explorer',
      subtitle: 'Dense vector search, BM25 keyword matching, and cross-encoder reranking',
    },
    graph: {
      title: 'Service Dependency Graph & Blast Radius',
      subtitle: 'Neo4j topology mapping, upstream/downstream impact, and cascade isolation',
    },
    github: {
      title: 'GitHub Repository & Commit Intelligence',
      subtitle: 'Recent commits, file diff inspection, and non-speculative incident correlation',
    },
    evaluation: {
      title: 'Evaluation & Benchmarking Engine',
      subtitle: 'Recall@k, MRR, NDCG@5, and multi-agent citation precision benchmarks',
    },
    settings: {
      title: 'System Settings & Architecture Configuration',
      subtitle: 'Vector DB, Neo4j, model parameters, and environment specifications',
    },
  };

  const current = titles[activeTab] || titles.overview;

  return (
    <header className="h-16 bg-dark-900/90 backdrop-blur-md border-b border-slate-800/80 px-6 flex items-center justify-between z-10 shrink-0">
      <div>
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          {current.title}
          <Badge variant="purple" size="sm">
            Production Ready
          </Badge>
        </h2>
        <p className="text-xs text-slate-400 font-mono">{current.subtitle}</p>
      </div>

      <div className="flex items-center gap-3">
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white border border-slate-700 text-xs transition-colors flex items-center gap-1.5"
            title="Refresh active view"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`}
            />
            <span className="hidden sm:inline font-mono">Refresh</span>
          </button>
        )}

        {onQuickInvestigate && activeTab !== 'investigations' && (
          <button
            onClick={onQuickInvestigate}
            className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-medium text-xs shadow-md shadow-indigo-600/20 transition-all flex items-center gap-1.5 font-mono"
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>New Investigation</span>
          </button>
        )}

        <div className="h-6 w-px bg-slate-800" />

        <a
          href="/api/v1/health"
          target="_blank"
          rel="noopener noreferrer"
          className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-slate-400 hover:text-slate-200 border border-slate-700 transition-colors"
          title="Open API Health Probe"
        >
          <Activity className="w-3.5 h-3.5" />
        </a>

        <a
          href="/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white border border-slate-700 text-xs transition-colors font-mono"
          title="Swagger OpenAPI Docs"
        >
          <span>API Docs</span>
          <ExternalLink className="w-3 h-3 text-slate-400" />
        </a>
      </div>
    </header>
  );
};

