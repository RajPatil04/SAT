// frontend/src/pages/SystemStatus.tsx
import React from 'react';
import { ModelStatus } from '../components/ModelStatus';

export const SystemStatus: React.FC = () => {
  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-main)', letterSpacing: '0.04em' }}>
          SYSTEM DIAGNOSTICS & FOUNDATION SPECIALIST REGISTRY
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
          Live telemetry reflecting backend API health, intelligent router state, and configured specialist endpoints.
        </p>
      </div>

      <ModelStatus />
    </div>
  );
};
