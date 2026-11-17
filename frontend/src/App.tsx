// frontend/src/App.tsx
import React, { useState, useEffect } from 'react';
import { Header, NavTab } from './components/Header';
import { Dashboard } from './pages/Dashboard';
import { ResearchDiagnostics } from './pages/ResearchDiagnostics';
import { RoutingConfigType } from './components/QueryInput';
import { SatQueryApiService } from './services/api';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('analyze');
  const [routingConfig, setRoutingConfig] = useState<RoutingConfigType>('CONFIG_C');
  const [systemOperational, setSystemOperational] = useState(true);

  useEffect(() => {
    async function checkBackend() {
      try {
        const res = await SatQueryApiService.checkHealth();
        setSystemOperational(res.status === 'online');
      } catch {
        setSystemOperational(false);
      }
    }
    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        systemOperational={systemOperational}
      />

      <main style={{ flex: 1, padding: '20px 16px' }}>
        {currentTab === 'analyze' && (
          <Dashboard
            routingConfig={routingConfig}
            onOpenResearch={() => setCurrentTab('research')}
          />
        )}
        {currentTab === 'research' && (
          <ResearchDiagnostics
            routingConfig={routingConfig}
            onSelectRoutingConfig={setRoutingConfig}
          />
        )}
      </main>

      <footer style={{
        borderTop: '1px solid var(--border-subtle)',
        padding: '16px 24px',
        textAlign: 'center',
        fontSize: 12,
        color: 'var(--text-dim)',
        background: 'rgba(13, 20, 34, 0.5)'
      }}>
        <div>SATQUERY AI • Query-Driven Routing & Evidence-Grounded Remote-Sensing Intelligence</div>
      </footer>
    </div>
  );
};

export default App;
