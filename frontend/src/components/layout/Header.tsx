import React, { useEffect, useState } from 'react';
import { NavTab } from './Sidebar';
import {
  Activity,
  ChevronRight,
  ExternalLink,
  Menu,
  Plus,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { Badge } from '../ui/Badge';
import { Button3D } from '../ui/Button3D';

interface HeaderProps {
  activeTab: NavTab;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  onQuickInvestigate?: () => void;
  onOpenMobileMenu?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onRefresh,
  isRefreshing = false,
  onQuickInvestigate,
  onOpenMobileMenu,
}) => {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (totalHeight > 0) {
        setScrollProgress(Math.min(100, Math.max(0, (window.scrollY / totalHeight) * 100)));
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const titles: Record<NavTab, { title: string; subtitle: string; breadcrumb: string }> = {
    overview: {
      title: 'Operations Dashboard',
      subtitle: 'System telemetry, recent investigations, and real-time infrastructure readiness',
      breadcrumb: 'Overview',
    },
    investigations: {
      title: 'Incident Investigations',
      subtitle: 'Ask what went wrong and investigate incidents using multi-agent AI and verified log evidence',
      breadcrumb: 'Investigations',
    },
    logs: {
      title: 'Log Explorer & Upload',
      subtitle: 'Upload application logs and perform hybrid keyword + semantic search',
      breadcrumb: 'Logs',
    },
    graph: {
      title: 'Service Dependency Graph & Blast Radius',
      subtitle: 'Interactive map of microservices, databases, and failure blast radius',
      breadcrumb: 'Service Graph',
    },
    github: {
      title: 'GitHub Intelligence & Code Changes',
      subtitle: 'Correlate recent git commits and code diffs with production incident errors',
      breadcrumb: 'GitHub',
    },
    evaluation: {
      title: 'Evaluation & Benchmarks',
      subtitle: 'Measurement of search accuracy, citation precision, and evidence groundedness',
      breadcrumb: 'Benchmarks',
    },
    settings: {
      title: 'Settings & Diagnostics',
      subtitle: 'Configuration for AI models, databases, vector stores, and connections',
      breadcrumb: 'Settings',
    },
  };

  const current = titles[activeTab] || titles.overview;

  return (
    <>
      {/* Apple-style Top Scroll Progress Indicator */}
      <div
        className="fixed top-0 left-0 h-[2.5px] bg-gradient-to-r from-electric-500 via-gold-400 to-electric-600 z-50 transition-all duration-150"
        style={{ width: `${scrollProgress}%` }}
      />

      <header className="h-18 bg-ivory-50/85 backdrop-blur-2xl border-b border-ivory-300/80 px-4 md:px-8 flex items-center justify-between z-20 shrink-0 sticky top-0 shadow-soft">
        {/* Left: Mobile Menu Trigger & Breadcrumb / Page Title */}
        <div className="flex items-center gap-3.5 min-w-0">
          <button
            onClick={onOpenMobileMenu}
            className="p-2 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-ivory-200/60 md:hidden transition-colors"
            title="Open Navigation Menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="min-w-0">
            {/* Breadcrumb with jewel divider */}
            <div className="hidden sm:flex items-center gap-2 text-[11px] uppercase tracking-wider text-slate-500 font-semibold mb-0.5">
              <span className="text-slate-400">DebugGraph AI</span>
              <ChevronRight className="w-3 h-3 text-gold-500" />
              <span className="text-slate-800 font-bold">{current.breadcrumb}</span>
            </div>

            <div className="flex items-center gap-3">
              <h2 className="text-base md:text-lg font-extrabold text-slate-950 truncate tracking-tight">
                {current.title}
              </h2>
              <Badge variant="success" size="sm" dot className="hidden md:inline-flex shadow-xs">
                Production Ready
              </Badge>
            </div>
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3 shrink-0">
          {/* Refresh Action */}
          {onRefresh && (
            <Button3D
              variant="surface"
              size="sm"
              onClick={onRefresh}
              disabled={isRefreshing}
              icon={
                <RefreshCw
                  className={`w-3.5 h-3.5 text-slate-500 ${isRefreshing ? 'animate-spin text-electric-500' : ''}`}
                />
              }
              title="Refresh Telemetry"
            >
              <span className="hidden sm:inline">Refresh</span>
            </Button3D>
          )}

          {/* Quick Investigation 3D Button */}
          {onQuickInvestigate && activeTab !== 'investigations' && (
            <Button3D
              variant="primary"
              size="sm"
              onClick={onQuickInvestigate}
              icon={<Plus className="w-3.5 h-3.5 text-white" />}
            >
              <span>New Investigation</span>
            </Button3D>
          )}

          <div className="hidden sm:block h-5 w-px bg-ivory-300" />

          {/* Health Probe link */}
          <a
            href="/api/v1/health"
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded-xl text-slate-500 hover:text-electric-600 hover:bg-electric-50 transition-colors"
            title="Live Subsystem Health Probe"
          >
            <Activity className="w-4 h-4" />
          </a>

          {/* Swagger OpenAPI Docs */}
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-slate-600 hover:text-electric-600 hover:bg-electric-50 text-xs font-semibold transition-colors border border-transparent hover:border-electric-200"
            title="Swagger OpenAPI Documentation"
          >
            <span>API Docs</span>
            <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
          </a>
        </div>
      </header>
    </>
  );
};
