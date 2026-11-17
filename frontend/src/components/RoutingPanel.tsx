// frontend/src/components/RoutingPanel.tsx
import React from 'react';
import { RoutingDecision } from '../types/api';

interface RoutingPanelProps {
  routing?: RoutingDecision | null;
  status: string;
}

export const RoutingPanel: React.FC<RoutingPanelProps> = ({ routing, status }) => {
  const steps = [
    { id: 'query', label: 'Query Input' },
    { id: 'input', label: 'Asset Analysis' },
    { id: 'task', label: 'Task Discovery' },
    { id: 'compat', label: 'Compatibility' },
    { id: 'router', label: 'Model Router' },
    { id: 'model', label: 'Specialist' },
    { id: 'exec', label: 'Inference' },
    { id: 'evidence', label: 'Evidence Fusion' },
    { id: 'answer', label: 'Answer' }
  ];

  const isCompleted = status === 'success';
  const isFailed = status === 'rejected_incompatible' || status === 'unavailable' || status === 'error';

  return (
    <div className="mc-card" style={{ marginBottom: 20 }}>
      <div className="mc-card-header">
        <span className="mc-card-title">
          <span>🧭</span> INTELLIGENT MODEL ROUTING ORCHESTRATION
        </span>
        {routing && (
          <span className="mc-badge mc-badge-cyan">
            {routing.detected_task} • {routing.detected_input_type}
          </span>
        )}
      </div>

      {/* Pipeline Stepper Flow */}
      <div className="mc-stepper">
        {steps.map((s, idx) => {
          const stepDone = isCompleted || (isFailed && idx <= 4);
          const isCurrent = !isCompleted && !isFailed && idx === 4;

          return (
            <React.Fragment key={s.id}>
              <div className={`mc-step-node ${stepDone ? 'completed' : ''} ${isCurrent ? 'active' : ''}`}>
                <div className="mc-step-circle">{stepDone ? '✓' : idx + 1}</div>
                <div className="mc-step-label">{s.label}</div>
              </div>
              {idx < steps.length - 1 && <span className="mc-step-arrow">→</span>}
            </React.Fragment>
          );
        })}
      </div>

      {routing && (
        <>
          {/* Rationale List */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>
              Routing Engine Rationale & Decision Trace
            </div>
            <ul style={{ paddingLeft: 18, fontSize: 13, color: 'var(--text-main)', lineHeight: 1.6 }}>
              {routing.reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>

          {/* Model Scoring Table */}
          {routing.candidate_scores && routing.candidate_scores.length > 0 && (
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                Proposed Query-Driven Formulation: Candidate Model Scores
              </div>
              <table className="mc-table">
                <thead>
                  <tr>
                    <th>Specialist Model</th>
                    <th>Formulation Score</th>
                    <th>Task Match</th>
                    <th>Input Match</th>
                    <th>Modality</th>
                    <th>Availability</th>
                  </tr>
                </thead>
                <tbody>
                  {routing.candidate_scores.map((cand) => {
                    const isSelected = cand.model_id === routing.selected_model_id;
                    return (
                      <tr key={cand.model_id} style={{ background: isSelected ? 'rgba(6, 182, 212, 0.1)' : undefined }}>
                        <td style={{ fontWeight: isSelected ? 600 : 400, color: isSelected ? 'var(--text-cyan)' : 'inherit' }}>
                          {isSelected && '▶ '}
                          {cand.display_name}
                        </td>
                        <td>
                          <span className={`mc-badge ${isSelected ? 'mc-badge-cyan' : 'mc-badge-blue'}`}>
                            {cand.total_score.toFixed(3)}
                          </span>
                        </td>
                        <td>{cand.task_match_score.toFixed(2)}</td>
                        <td>{cand.input_type_match_score.toFixed(2)}</td>
                        <td>{cand.modality_match_score.toFixed(2)}</td>
                        <td>
                          <span className={`mc-badge ${cand.availability_status === 'AVAILABLE' ? 'mc-badge-green' : cand.availability_status === 'MOCK' ? 'mc-badge-amber' : 'mc-badge-rose'}`}>
                            {cand.availability_status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
};
