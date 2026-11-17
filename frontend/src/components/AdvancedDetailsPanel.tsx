// frontend/src/components/AdvancedDetailsPanel.tsx
import React, { useState } from 'react';
import { AnalysisResponse } from '../types/api';
import { ExecutionTrace } from './ExecutionTrace';
import { ReportDownload } from './ReportDownload';

interface AdvancedDetailsPanelProps {
  response: AnalysisResponse;
}

export const AdvancedDetailsPanel: React.FC<AdvancedDetailsPanelProps> = ({ response }) => {
  const [showTrace, setShowTrace] = useState(false);

  const timings = response.timings || {};
  const metadata = response.metadata || [];
  const validation = response.validation;
  const compatibility = response.compatibility;
  const routing = response.routing;

  const hasTechnicalErrors = Boolean(
    routing?.blocking_issue ||
    response.status !== 'success' ||
    (validation?.blocking_errors && validation.blocking_errors.length > 0)
  );

  return (
    <div className="sat-advanced-panel">
      {/* 1. Technical Errors & Diagnostic Alerts (When relevant) */}
      {hasTechnicalErrors && (
        <div className="mc-card sat-technical-error-card">
          <div className="mc-card-header" style={{ marginBottom: 8, paddingBottom: 6 }}>
            <span className="mc-card-title" style={{ fontSize: 13, color: '#f43f5e' }}>
              <span>⚠️</span> Technical Issues & Blocking Errors
            </span>
            <span className="mc-badge mc-badge-rose">{response.status.toUpperCase()}</span>
          </div>

          {routing?.blocking_issue && (
            <div style={{ fontSize: 13, color: '#fecdd3', marginBottom: 8 }}>
              <b>Blocking Issue:</b> {routing.blocking_issue}
            </div>
          )}

          {validation?.blocking_errors && validation.blocking_errors.length > 0 && (
            <div style={{ fontSize: 12, color: '#fecdd3' }}>
              <b>Validation Blocking Errors:</b>
              <ul style={{ paddingLeft: 18, marginTop: 4 }}>
                {validation.blocking_errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* 2. Model Lifecycle & Execution Telemetry: Selected, Loaded, Executed, Failed/Skipped */}
      <div className="mc-card" style={{ padding: '16px 20px' }}>
        <div className="mc-card-header" style={{ marginBottom: 12, paddingBottom: 8 }}>
          <span className="mc-card-title" style={{ fontSize: 13 }}>
            <span>🧭</span> Model Lifecycle & Execution Telemetry
          </span>
          <div style={{ display: 'flex', gap: 6 }}>
            {response.routing_config && (
              <span className="mc-badge mc-badge-blue">{response.routing_config}</span>
            )}
          </div>
        </div>

        {/* 4 Separate Statuses */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10, marginBottom: 14 }}>
          {/* 1. Model Selected */}
          <div style={{ background: 'var(--bg-card)', padding: '10px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>1. Model Selected</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent-sky)', marginTop: 4 }}>
              {(response.selected_models && response.selected_models.length > 0)
                ? response.selected_models.join(', ')
                : (routing?.selected_model_name || 'None')}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
              Task: {response.task_type || response.task}
            </div>
          </div>

          {/* 2. Model Loaded */}
          <div style={{ background: 'var(--bg-card)', padding: '10px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>2. Model Loaded</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#10b981', marginTop: 4 }}>
              {(response.models_used && response.models_used.length > 0)
                ? response.models_used.join(', ')
                : (routing?.selected_model_name ? `${routing.selected_model_name} (Ready)` : 'None')}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
              Weights / Microservice Online
            </div>
          </div>

          {/* 3. Inference Executed */}
          <div style={{ background: 'var(--bg-card)', padding: '10px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>3. Inference Executed</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: (response.models_used && response.models_used.length > 0) ? '#10b981' : '#f43f5e', marginTop: 4 }}>
              {(response.models_used && response.models_used.length > 0)
                ? response.models_used.join(', ')
                : 'None Executed'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
              {timings.model_inference_ms !== undefined ? `${timings.model_inference_ms.toFixed(1)} ms runtime` : 'No execution output'}
            </div>
          </div>

          {/* 4. Inference Failed / Skipped */}
          <div style={{ background: 'var(--bg-card)', padding: '10px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>4. Inference Failed / Skipped</div>
            {(() => {
              const selected = (response.selected_models && response.selected_models.length > 0)
                ? response.selected_models
                : (routing?.selected_model_name ? [routing.selected_model_name] : []);
              const used = response.models_used || [];
              const skipped = selected.filter(m => !used.includes(m));
              return (
                <>
                  <div style={{ fontSize: 13, fontWeight: 600, color: skipped.length > 0 ? '#f59e0b' : 'var(--text-muted)', marginTop: 4 }}>
                    {skipped.length > 0 ? skipped.join(', ') : 'None (All Completed)'}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
                    {skipped.length > 0 ? 'Unconfigured endpoint; skipped honestly' : 'No execution dropped'}
                  </div>
                </>
              );
            })()}
          </div>
        </div>

        {/* Routing Rationale */}
        {routing?.reasons && routing.reasons.length > 0 && (
          <div style={{ background: 'var(--bg-card)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: 6 }}>
              Routing Logic & Decision Factors
            </div>
            <ul style={{ paddingLeft: 18, fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5, margin: 0 }}>
              {routing.reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* 3. Processing Time & Timings Breakdown */}
      <div className="mc-card" style={{ padding: '16px 20px' }}>
        <div className="mc-card-header" style={{ marginBottom: 12, paddingBottom: 8 }}>
          <span className="mc-card-title" style={{ fontSize: 13 }}>
            <span>⏱️</span> Processing Time Breakdown
          </span>
          <span className="mc-badge mc-badge-green">
            Total: {response.total_duration_ms ? response.total_duration_ms.toFixed(1) : '0.0'} ms
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 8 }}>
          {timings.validation_ms !== undefined && (
            <div style={{ background: 'var(--bg-card)', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>Validation Stage</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-main)', marginTop: 2 }}>
                {timings.validation_ms.toFixed(1)} ms
              </div>
            </div>
          )}
          {timings.routing_ms !== undefined && (
            <div style={{ background: 'var(--bg-card)', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>Routing Stage</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-main)', marginTop: 2 }}>
                {timings.routing_ms.toFixed(1)} ms
              </div>
            </div>
          )}
          {timings.model_inference_ms !== undefined && (
            <div style={{ background: 'var(--bg-card)', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>Model Inference</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--accent-sky)', marginTop: 2 }}>
                {timings.model_inference_ms.toFixed(1)} ms
              </div>
            </div>
          )}
          {timings.cross_reasoning_ms !== undefined && timings.cross_reasoning_ms > 0 && (
            <div style={{ background: 'var(--bg-card)', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>Cross-Reasoning</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#c084fc', marginTop: 2 }}>
                {timings.cross_reasoning_ms.toFixed(1)} ms
              </div>
            </div>
          )}
          <div style={{ background: 'var(--bg-card)', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>Total Processing Time</div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#10b981', marginTop: 2 }}>
              {response.total_duration_ms ? response.total_duration_ms.toFixed(1) : '0.0'} ms
            </div>
          </div>
        </div>
      </div>

      {/* 4. Input Validation Results & Image Metadata */}
      <div className="mc-card" style={{ padding: '16px 20px' }}>
        <div className="mc-card-header" style={{ marginBottom: 12, paddingBottom: 8 }}>
          <span className="mc-card-title" style={{ fontSize: 13 }}>
            <span>📊</span> Input Validation & Detected Image Metadata
          </span>
          {validation && (
            <span className={`mc-badge ${validation.is_valid ? 'mc-badge-green' : 'mc-badge-rose'}`}>
              {validation.is_valid ? 'VALIDATED' : 'WARNINGS'}
            </span>
          )}
        </div>

        {/* Validation Flags */}
        {validation && (
          <div style={{ display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
            {validation.spatial_aligned !== undefined && validation.spatial_aligned !== null && (
              <span className={`mc-badge ${validation.spatial_aligned ? 'mc-badge-green' : 'mc-badge-amber'}`}>
                {validation.spatial_aligned ? '✓ Dimensions Aligned' : '⚠️ Spatial Misaligned'}
              </span>
            )}
            {validation.modality_compatible !== undefined && validation.modality_compatible !== null && (
              <span className={`mc-badge ${validation.modality_compatible ? 'mc-badge-green' : 'mc-badge-rose'}`}>
                {validation.modality_compatible ? '✓ Modality Verified' : '⚠️ Modality Incompatible'}
              </span>
            )}
          </div>
        )}

        {/* Detected Image Metadata Cards */}
        {metadata.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 10 }}>
            {metadata.map((m, idx) => (
              <div key={idx} style={{ background: 'var(--bg-card)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontWeight: 600, fontSize: 12, color: 'var(--text-cyan)' }}>{m.filename}</span>
                  <span className="mc-badge mc-badge-blue">{m.format}</span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
                  <div><b>Dimensions:</b> {m.width}×{m.height}</div>
                  <div><b>Bands:</b> {m.channels} ({m.datatype})</div>
                  <div><b>Detected Modality:</b> {m.detected_modality}</div>
                  <div><b>GeoTIFF Georef:</b> {m.is_geotiff ? 'Yes' : 'No'}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 5. Image Compatibility Information */}
      {compatibility && (
        <div className="mc-card" style={{ padding: '16px 20px' }}>
          <div className="mc-card-header" style={{ marginBottom: 10, paddingBottom: 6 }}>
            <span className="mc-card-title" style={{ fontSize: 13 }}>
              <span>🔗</span> Image Compatibility Information
            </span>
            <span className={`mc-badge ${compatibility.is_compatible ? 'mc-badge-green' : 'mc-badge-rose'}`}>
              {compatibility.is_compatible ? 'COMPATIBLE' : 'DISCREPANCY'}
            </span>
          </div>

          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>
            <b>Input Structure:</b> {compatibility.input_type} • <b>Physical Modality:</b> {compatibility.modality}
          </div>

          {compatibility.validation_messages && compatibility.validation_messages.length > 0 && (
            <ul style={{ paddingLeft: 18, fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>
              {compatibility.validation_messages.map((msg, i) => (
                <li key={i}>{msg}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* 6. Confidence Information (Genuinely documented only) */}
      <div className="mc-card" style={{ padding: '16px 20px' }}>
        <div className="mc-card-header" style={{ marginBottom: 12, paddingBottom: 8 }}>
          <span className="mc-card-title" style={{ fontSize: 13 }}>
            <span>🎯</span> Calibrated Confidence & Probability
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
          <div style={{ background: 'var(--bg-card)', padding: '10px 14px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Router Intent Confidence</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--accent-sky)', marginTop: 2 }}>
              {response.router_confidence !== null && response.router_confidence !== undefined
                ? `${(response.router_confidence * 100).toFixed(1)}%`
                : 'N/A'}
            </div>
          </div>

          <div style={{ background: 'var(--bg-card)', padding: '10px 14px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Specialist Model Confidence</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: response.confidence ? 'var(--accent-emerald)' : 'var(--text-muted)', marginTop: 2 }}>
              {response.confidence !== null && response.confidence !== undefined
                ? `${(response.confidence * 100).toFixed(1)}% (Documented)`
                : 'Not calibrated / unprovided'}
            </div>
          </div>
        </div>
      </div>

      {/* 7. Limitations & Scientific Caveats */}
      {response.limitations && response.limitations.length > 0 && (
        <div className="mc-card" style={{ padding: '16px 20px' }}>
          <div className="mc-card-header" style={{ marginBottom: 10, paddingBottom: 6 }}>
            <span className="mc-card-title" style={{ fontSize: 13 }}>
              <span>⚠️</span> Limitations & Scientific Caveats
            </span>
          </div>

          <ul style={{ paddingLeft: 18, fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>
            {response.limitations.map((lim, i) => (
              <li key={i}>{lim}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 8. Downstream Analytical Findings & Feature Telemetry */}
      {response.evidence?.downstream_findings && (
        <div className="mc-card" style={{ padding: '16px 20px' }}>
          <div className="mc-card-header" style={{ marginBottom: 12, paddingBottom: 8 }}>
            <span className="mc-card-title" style={{ fontSize: 13 }}>
              <span>🔬</span> Downstream Analysis & Latent Representation Metrics
            </span>
            <span className="mc-badge mc-badge-cyan">
              {response.evidence.downstream_findings.model_name}
            </span>
          </div>

          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>
            {response.evidence.downstream_findings.findings_summary}
          </div>

          {response.evidence.downstream_findings.metrics && Object.keys(response.evidence.downstream_findings.metrics).length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 8 }}>
              {Object.entries(response.evidence.downstream_findings.metrics).map(([k, v]) => {
                if (v === null || v === undefined) return null;
                const formattedKey = k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                const valStr = typeof v === 'number' ? (Number.isInteger(v) ? v.toLocaleString() : v.toFixed(4)) : String(v);
                return (
                  <div key={k} style={{ background: 'var(--bg-card)', padding: '8px 10px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>{formattedKey}</div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent-sky)', marginTop: 2 }}>
                      {valStr}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* 9. Model Execution Details (Step-by-Step Trace) */}
      <div className="mc-card" style={{ padding: '16px 20px' }}>
        <div
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
          onClick={() => setShowTrace(!showTrace)}
        >
          <span className="mc-card-title" style={{ fontSize: 13 }}>
            <span>📜</span> Model Execution Details ({Array.isArray(response.execution_trace) ? response.execution_trace.length : 0} stages)
          </span>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            {showTrace ? '▲ Collapse Trace' : '▼ Expand Trace'}
          </span>
        </div>

        {showTrace && (
          <div style={{ marginTop: 14 }}>
            <ExecutionTrace trace={response.execution_trace} />
          </div>
        )}
      </div>

      {/* 9. Report Export */}
      <ReportDownload requestId={response.request_id} />
    </div>
  );
};
