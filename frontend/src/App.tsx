import React, { useEffect, useState } from 'react';
import { Sidebar, NavTab } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { OverviewPage } from './pages/OverviewPage';
import { InvestigationsPage } from './pages/InvestigationsPage';
import { LogExplorerPage } from './pages/LogExplorerPage';
import { DependencyGraphPage } from './pages/DependencyGraphPage';
import { GitHubPage } from './pages/GitHubPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { SettingsPage } from './pages/SettingsPage';
import { api } from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('overview');
  const [systemHealthy, setSystemHealthy] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  // Investigation pre-fill state when launched from demo query or overview
  const [investigationQuery, setInvestigationQuery] = useState<string>('');
  const [investigationService, setInvestigationService] = useState<string>('');

  const checkHealth = async () => {
    try {
      const h = await api.getHealth();
      setSystemHealthy(h.status === 'ok' || h.status === 'healthy');
    } catch {
      setSystemHealthy(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await checkHealth();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const handleLaunchDemoQuery = (query: string, service?: string) => {
    setInvestigationQuery(query);
    setInvestigationService(service || '');
    setActiveTab('investigations');
  };

  const handleQuickInvestigate = () => {
    setInvestigationQuery('Investigate active production incidents');
    setInvestigationService('');
    setActiveTab('investigations');
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-800 antialiased font-sans">
      {/* Left Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        systemHealthy={systemHealthy}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-slate-50">
        {/* Global Header */}
        <Header
          activeTab={activeTab}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
          onQuickInvestigate={handleQuickInvestigate}
          onOpenMobileMenu={() => setMobileMenuOpen(true)}
        />

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto px-4 md:px-8 py-6">
          <div className="max-w-7xl mx-auto pb-12">
            {activeTab === 'overview' && (
              <OverviewPage
                onNavigate={setActiveTab}
                onLaunchDemoQuery={handleLaunchDemoQuery}
              />
            )}
            {activeTab === 'investigations' && (
              <InvestigationsPage
                key={`${investigationQuery}-${investigationService}`}
                initialQuery={investigationQuery}
                initialService={investigationService}
              />
            )}
            {activeTab === 'logs' && <LogExplorerPage />}
            {activeTab === 'graph' && <DependencyGraphPage />}
            {activeTab === 'github' && <GitHubPage />}
            {activeTab === 'evaluation' && <EvaluationPage />}
            {activeTab === 'settings' && <SettingsPage />}
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;
