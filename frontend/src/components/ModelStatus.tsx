// frontend/src/components/ModelStatus.tsx
import React, { useEffect, useState } from 'react';
import { ModelInfoResponse, SystemStatusResponse } from '../types/api';
import { SatQueryApiService } from '../services/api';

export const ModelStatus: React.FC = () => {
  const [models, setModels] = useState<ModelInfoResponse[]>([]);
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [mList, sysStatus] = await Promise.all([
          SatQueryApiService.getModels(),
          SatQueryApiService.getSystemStatus()
        ]);
        setModels(mList);
        setStatus(sysStatus);
      } catch (e) {
        console.error('Failed to load status:', e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return <div style={{ color: 'var(--text-muted)', padding: 20 }}>Loading system diagnostics...</div>;
  }

  const getStatusBadge = (st: string) => {
    switch (st) {
      case 'AVAILABLE':
      case 'ONLINE':
        return <span className="mc-badge mc-badge-green">ONLINE</span>;
      case 'MOCK':
        return <span className="mc-badge mc-badge-amber">MOCK (SIMULATED)</span>;
      case 'NOT_CONFIGURED':
        return <span className="mc-badge mc-badge-blue">NOT CONFIGURED</span>;
      case 'UNAVAILABLE':
      case 'OFFLINE':
      default:
        return <span className="mc-badge mc-badge-rose">{st}</span>;
    }
  };

  return (
    <div>
      {/* System Infrastructure Telemetry */}
      {status && (
        <div className="mc-card" style={{ marginBottom: 20 }}>
          <div className="mc-card-header">
            <span className="mc-card-title">
              <span>🖥️</span> CORE FRAMEWORK INFRASTRUCTURE
            </span>
            <span className="mc-badge mc-badge-green">STATUS: {status.status}</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
            <div style={{ background: 'var(--bg-card)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase' }}>FastAPI Backend</div>
              <div style={{ marginTop: 4 }}>{getStatusBadge(status.fastapi)}</div>
            </div>

            <div style={{ background: 'var(--bg-card)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Intelligent Router Engine</div>
              <div style={{ marginTop: 4 }}>{getStatusBadge(status.router)}</div>
            </div>

            <div style={{ background: 'var(--bg-card)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase' }}>SQLite Telemetry DB</div>
              <div style={{ marginTop: 4 }}>{getStatusBadge(status.database)}</div>
            </div>

            <div style={{ background: 'var(--bg-card)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Experiment Logger</div>
              <div style={{ marginTop: 4 }}>{getStatusBadge(status.experiment_logger)}</div>
              <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>{status.active_experiments_count} logged experiments</div>
            </div>
          </div>
        </div>
      )}

      {/* Model Specialist Registry */}
      <div className="mc-card">
        <div className="mc-card-header">
          <span className="mc-card-title">
            <span>🛰️</span> SPECIALIST FOUNDATION MODEL REGISTRY
          </span>
          <span className="mc-badge mc-badge-cyan">{models.length} Specialists Configured</span>
        </div>

        <table className="mc-table">
          <thead>
            <tr>
              <th>Specialist Model</th>
              <th>Status</th>
              <th>Supported Tasks</th>
              <th>Input Structures</th>
              <th>Sensors / Modalities</th>
              <th>Protocol / API</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m) => (
              <tr key={m.model_id}>
                <td>
                  <div style={{ fontWeight: 600, color: '#fff' }}>{m.display_name}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>{m.description}</div>
                  {m.paper_reference && (
                    <div style={{ fontSize: 10, color: 'var(--accent-sky)', marginTop: 2 }}>Ref: {m.paper_reference}</div>
                  )}
                </td>
                <td>{getStatusBadge(m.status)}</td>
                <td>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {m.tasks.map((t) => (
                      <span key={t} className="mc-badge mc-badge-blue">{t}</span>
                    ))}
                  </div>
                </td>
                <td>
                  {m.input_types.map((i) => (
                    <div key={i} style={{ fontSize: 11, color: 'var(--text-muted)' }}>• {i}</div>
                  ))}
                </td>
                <td>
                  {m.modalities.map((mod) => (
                    <span key={mod} className="mc-badge mc-badge-cyan" style={{ marginRight: 4 }}>{mod}</span>
                  ))}
                </td>
                <td>
                  <span className="mc-badge mc-badge-amber">{m.endpoint_type.toUpperCase()}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
