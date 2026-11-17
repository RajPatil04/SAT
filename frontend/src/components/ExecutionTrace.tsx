// frontend/src/components/ExecutionTrace.tsx
import React, { useState } from 'react';
import { ExecutionStep } from '../types/api';

interface ExecutionTraceProps {
  trace: ExecutionStep[];
}

export const ExecutionTrace: React.FC<ExecutionTraceProps> = ({ trace }) => {
  const [isOpen, setIsOpen] = useState(true);
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  if (!trace || trace.length === 0) return null;

  return (
    <div className="mc-card" style={{ marginBottom: 20 }}>
      <div
        className="mc-card-header"
        style={{ cursor: 'pointer', userSelect: 'none' }}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="mc-card-title">
          <span>⏱️</span> BACKEND AGENTIC EXECUTION TRACE
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="mc-badge mc-badge-blue">{trace.length} Sequenced Events</span>
          <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>
            {isOpen ? '▲ Collapse' : '▼ Expand'}
          </span>
        </div>
      </div>

      {isOpen && (
        <div className="mc-trace-list">
          {trace.map((step) => {
            const isExpanded = expandedStep === step.step;
            const statusClass = step.status === 'completed' ? 'mc-badge-green' : step.status === 'failed' ? 'mc-badge-rose' : 'mc-badge-blue';

            return (
              <div
                key={step.step}
                className="mc-trace-item"
                onClick={() => setExpandedStep(isExpanded ? null : step.step)}
                style={{ cursor: step.details ? 'pointer' : 'default' }}
              >
                <div className="mc-trace-step">{step.step}</div>
                <div className="mc-trace-content">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{step.component}</span>
                    <span className={`mc-badge ${statusClass}`}>{step.status}</span>
                    {step.details && (
                      <span style={{ fontSize: 10, color: 'var(--accent-cyan)' }}>
                        {isExpanded ? '▲ Hide Details' : '▼ View Details'}
                      </span>
                    )}
                  </div>
                  <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{step.message}</div>
                  {isExpanded && step.details && (
                    <pre style={{ marginTop: 8, padding: 8, background: '#080c14', borderRadius: 4, fontSize: 11, color: 'var(--accent-cyan)', overflowX: 'auto' }}>
                      {JSON.stringify(step.details, null, 2)}
                    </pre>
                  )}
                </div>
                <div className="mc-trace-duration">{step.duration_ms.toFixed(1)} ms</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
