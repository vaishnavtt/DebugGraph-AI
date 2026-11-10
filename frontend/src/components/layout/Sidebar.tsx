import React from 'react';
import {
  BarChart3,
  ChevronLeft,
  ChevronRight,
  FileText,
  GitBranch,
  LayoutDashboard,
  Network,
  Search,
  Settings,
  Sparkles,
  X,
  Compass,
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
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  systemHealthy = true,
  collapsed = false,
  onToggleCollapse,
  mobileOpen = false,
  onCloseMobile,
}) => {
  const navItems = [
    {
      id: 'overview' as NavTab,
      label: 'Overview',
      icon: LayoutDashboard,
      desc: 'Operations command center',
    },
    {
      id: 'investigations' as NavTab,
      label: 'Investigations',
      icon: Search,
      desc: 'LangGraph multi-agent RCA',
      badge: 'Multi-Agent',
    },
    {
      id: 'logs' as NavTab,
      label: 'Log Explorer',
      icon: FileText,
      desc: 'Ingestion & hybrid search',
    },
    {
      id: 'graph' as NavTab,
      label: 'Service Graph',
      icon: Network,
      desc: 'Topology & blast radius',
    },
    {
      id: 'github' as NavTab,
      label: 'GitHub Intelligence',
      icon: GitBranch,
      desc: 'Code mutations & diffs',
    },
    {
      id: 'evaluation' as NavTab,
      label: 'Evaluation & Benchmarks',
      icon: BarChart3,
      desc: 'Precision & groundedness',
    },
    {
      id: 'settings' as NavTab,
      label: 'Settings',
      icon: Settings,
      desc: 'Subsystem configurations',
    },
  ];

  const handleNavClick = (id: NavTab) => {
    onTabChange(id);
    if (onCloseMobile) onCloseMobile();
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {mobileOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-midnight-950/70 backdrop-blur-md md:hidden transition-opacity"
        />
      )}

      {/* Sidebar Chassis */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 flex flex-col justify-between bg-midnight-950 text-ivory-50 border-r border-midnight-800 shadow-2xl transition-all duration-300 ease-in-out select-none ${
          collapsed ? 'w-20' : 'w-72'
        } ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Top Header & Navigation */}
        <div>
          {/* Brand Emblem */}
          <div className="h-18 flex items-center justify-between px-4 border-b border-midnight-800/80 bg-gradient-to-b from-midnight-900 to-midnight-950">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-gold-400 via-gold-500 to-amber-700 flex items-center justify-center shadow-glow-gold shrink-0 border border-gold-300/40">
                <Compass className="w-5 h-5 text-midnight-950" />
              </div>
              {!collapsed && (
                <div className="truncate">
                  <div className="font-extrabold text-sm tracking-tight text-ivory-50 flex items-center gap-1.5">
                    <span>DebugGraph</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-gold-500/20 text-gold-300 font-mono font-bold border border-gold-500/30">
                      AI
                    </span>
                  </div>
                  <p className="text-[10px] uppercase tracking-widest text-gold-500/80 font-bold mt-0.5">
                    Incident Intelligence
                  </p>
                </div>
              )}
            </div>

            {/* Mobile Close Button */}
            <button
              onClick={onCloseMobile}
              className="p-1.5 rounded-lg text-slate-400 hover:text-ivory-50 hover:bg-midnight-800 md:hidden"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Items */}
          <nav className="p-3 space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  title={collapsed ? item.label : undefined}
                  className={`w-full flex items-center gap-3.5 px-3 py-2.5 rounded-2xl text-left text-xs sm:text-sm transition-all duration-200 group relative ${
                    isActive
                      ? 'bg-gradient-to-r from-electric-600/30 via-electric-500/20 to-transparent text-white font-bold border-l-2 border-electric-400 shadow-sm'
                      : 'text-slate-400 hover:text-ivory-100 hover:bg-midnight-900/80 font-medium'
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 transition-colors ${
                      isActive
                        ? 'bg-electric-500 text-white shadow-glow-electric'
                        : 'bg-midnight-900 border border-midnight-800 text-slate-400 group-hover:text-gold-400 group-hover:border-gold-500/30'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>

                  {!collapsed && (
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="truncate">{item.label}</span>
                        {item.badge && (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-gold-500/20 text-gold-300 font-bold border border-gold-500/30">
                            {item.badge}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 truncate font-normal">
                        {item.desc}
                      </p>
                    </div>
                  )}

                  {/* Active Pip Indicator */}
                  {isActive && (
                    <span className="absolute right-2.5 w-1.5 h-1.5 rounded-full bg-gold-400 shadow-glow-gold" />
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom Rail: System Status & Collapse Toggle */}
        <div className="p-3 border-t border-midnight-800/80 bg-midnight-900/40">
          {!collapsed && (
            <div className="p-3 rounded-2xl bg-midnight-900/80 border border-midnight-800 mb-2">
              <div className="flex items-center justify-between text-xs font-semibold mb-1">
                <span className="text-slate-400">Telemetry Engine</span>
                <span
                  className={`flex items-center gap-1.5 text-[11px] font-bold ${
                    systemHealthy ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  <span
                    className={`w-2 h-2 rounded-full ${
                      systemHealthy
                        ? 'bg-emerald-400 shadow-[0_0_8px_#34D399]'
                        : 'bg-rose-400 shadow-[0_0_8px_#F87171]'
                    }`}
                  />
                  {systemHealthy ? 'Connected' : 'Degraded'}
                </span>
              </div>
              <p className="text-[10px] text-slate-400 leading-tight">
                LangGraph 7-Agent Orchestrator Active
              </p>
            </div>
          )}

          {/* Desktop Collapse Rail Toggle */}
          {onToggleCollapse && (
            <button
              onClick={onToggleCollapse}
              className="w-full flex items-center justify-center p-2 rounded-xl text-slate-400 hover:text-ivory-50 hover:bg-midnight-900 transition-colors hidden md:flex"
              title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            >
              {collapsed ? (
                <ChevronRight className="w-4 h-4 text-gold-400" />
              ) : (
                <div className="flex items-center gap-2 text-xs font-semibold">
                  <ChevronLeft className="w-4 h-4" />
                  <span>Collapse Rail</span>
                </div>
              )}
            </button>
          )}
        </div>
      </aside>
    </>
  );
};
