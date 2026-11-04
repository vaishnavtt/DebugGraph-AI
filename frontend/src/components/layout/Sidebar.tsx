import React from 'react';
import {
  BarChart3,
  FileText,
  GitBranch,
  LayoutDashboard,
  Network,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';

export type NavTab =
  | 'overview'
  | 'investigations'
  | 'logs'
  | 'graph'
  | 'github'
  | 'evaluation'
  | 'settings';

interface SidebarProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  systemHealthy?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  systemHealthy = true,
}) => {
  const navItems = [
    {
      id: 'overview' as NavTab,
      label: 'Overview',
      icon: LayoutDashboard,
      desc: 'Operations Center',
    },
    {
      id: 'investigations' as NavTab,
      label: 'Investigations',
      icon: Search,
      desc: 'LangGraph & RCA',
      badge: 'Multi-Agent',
    },
    {
      id: 'logs' as NavTab,
      label: 'Log Explorer',
      icon: FileText,
      desc: 'Ingestion & Hybrid Search',
    },
    {
      id: 'graph' as NavTab,
      label: 'Service Graph',
      icon: Network,
      desc: 'Neo4j & Blast Radius',
    },
    {
      id: 'github' as NavTab,
      label: 'GitHub Intelligence',
      icon: GitBranch,
      desc: 'Commits & Diff Analyzer',
    },
    {
      id: 'evaluation' as NavTab,
      label: 'Evaluation & Benchmarks',
      icon: BarChart3,
      desc: 'Recall & Groundedness',
    },
    {
      id: 'settings' as NavTab,
      label: 'Settings',
      icon: Settings,
      desc: 'System Configuration',
    },
  ];

  return (
    <aside className="w-64 bg-dark-900 border-r border-slate-800/80 flex flex-col justify-between shrink-0 select-none">
      {/* Brand Header */}
      <div>
        <div className="h-16 flex items-center px-5 border-b border-slate-800/80 gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-extrabold text-sm tracking-wide text-white flex items-center gap-1.5">
              DebugGraph <span className="text-cyan-400 font-semibold">AI</span>
            </h1>
            <p className="text-[10px] text-slate-400 font-mono tracking-tight">
              AGENTIC INCIDENT RCA
            </p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left text-sm transition-all duration-150 ${
                  isActive
                    ? 'bg-indigo-600/20 text-cyan-300 border border-indigo-500/30 font-medium'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Icon
                  className={`w-4 h-4 shrink-0 ${
                    isActive ? 'text-cyan-400' : 'text-slate-400'
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="truncate">{item.label}</span>
                    {item.badge && (
                      <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {item.badge}
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-slate-400 truncate font-mono">
                    {item.desc}
                  </div>
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Status */}
      <div className="p-4 border-t border-slate-800/80 bg-dark-950/40">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                systemHealthy ? 'bg-emerald-400 shadow-sm shadow-emerald-400' : 'bg-amber-400'
              }`}
            />
            <span className="text-xs text-slate-300 font-mono">
              {systemHealthy ? 'System Operational' : 'Degraded State'}
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">v0.1.0</span>
        </div>
        <div className="mt-2 text-[11px] text-slate-400 flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Evidence Grounded RCA</span>
        </div>
      </div>
    </aside>
  );
};

