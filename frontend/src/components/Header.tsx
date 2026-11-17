// frontend/src/components/Header.tsx
import React from 'react';

export type NavTab = 'analyze' | 'research';

interface HeaderProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  systemOperational: boolean;
}

export const Header: React.FC<HeaderProps> = ({ currentTab, onSelectTab, systemOperational }) => {
  return (
    <header className="mc-header">
      <div className="mc-logo-group">
        <div className="sat-globe-wrapper">
          <img src="/globe_logo_clean.png" alt="SatQuery AI Globe" className="sat-globe-img" />
        </div>
        <div className="mc-title-box">
          <h1>
            SATQUERY <span>AI</span>
          </h1>
          <p>Satellite Vision-Language Intelligence Platform</p>
        </div>
      </div>

      <nav className="mc-nav">
        <button
          className={`mc-nav-btn ${currentTab === 'analyze' ? 'active' : ''}`}
          onClick={() => onSelectTab('analyze')}
        >
          <span style={{ marginRight: 6 }}>📊</span> Analyze
        </button>
        <button
          className={`mc-nav-btn ${currentTab === 'research' ? 'active' : ''}`}
          onClick={() => onSelectTab('research')}
        >
          <span style={{ marginRight: 6 }}>🔬</span> Research & Diagnostics
        </button>
      </nav>

      <div className="mc-telemetry">
        <div className="mc-status-pill">
          <span className="mc-status-dot" style={{ background: systemOperational ? '#22c55e' : '#f59e0b' }} />
          <span>{systemOperational ? 'SYSTEM ONLINE' : 'SYSTEM STANDBY'}</span>
        </div>
      </div>
    </header>
  );
};
