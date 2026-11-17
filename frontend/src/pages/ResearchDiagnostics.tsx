// frontend/src/pages/ResearchDiagnostics.tsx
import React, { useEffect, useState } from 'react';
import { ExperimentSummary, SystemMetrics } from '../types/api';
import { RoutingConfigType } from '../components/QueryInput';
import { ModelStatus } from '../components/ModelStatus';
import { SatQueryApiService } from '../services/api';

interface ResearchDiagnosticsProps {
  routingConfig: RoutingConfigType;
  onSelectRoutingConfig: (cfg: RoutingConfigType) => void;
}

export const ResearchDiagnostics: React.FC<ResearchDiagnosticsProps> = ({
  routingConfig,
  onSelectRoutingConfig
}) => {
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [benchmarkResult, setBenchmarkResult] = useState<any | null>(null);
  const [tableIIResult, setTableIIResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [benchmarking, setBenchmarking] = useState(false);
  const [tableIILoading, setTableIILoading] = useState(false);

  const loadData = async () => {
    try {
      const [expList, met] = await Promise.all([
        SatQueryApiService.getExperiments(),
        SatQueryApiService.getMetrics()
      ]);
      setExperiments(expList);
      setMetrics(met);
    } catch (e) {
      console.error('Failed to load experiments telemetry:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunBenchmark = async () => {
    setBenchmarking(true);
    try {
      const res = await SatQueryApiService.runBenchmark();
      setBenchmarkResult(res);
      await loadData();
    } catch (e) {
      console.error('Benchmark suite execution failed:', e);
    } finally {
      setBenchmarking(false);
    }
  };

  const handleRunTableII = async () => {
    setTableIILoading(true);
    try {
      const res = await SatQueryApiService.runTableIIEvaluation();
      setTableIIResult(res);
    } catch (e) {
      console.error('Table II evaluation failed:', e);
    } finally {
      setTableIILoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24, maxWidth: 1200, margin: '0 auto', padding: '12px 16px' }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-main)', letterSpacing: '0.04em' }}>
          🔬 RESEARCH & DIAGNOSTICS HUB
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
          Comparative evaluation of routing configurations, specialist model registry, empirical benchmarks, and experiment telemetry.
        </p>
      </div>

      {/* 1. Routing Strategy Comparison & Configuration (Section 4 & 8) */}
      <div className="mc-card">
        <div className="mc-card-header">
          <span className="mc-card-title">
            <span>⚙️</span> ROUTING STRATEGY COMPARISON & SELECTION
          </span>
          <span className="mc-badge mc-badge-cyan">Active: {routingConfig}</span>
        </div>

        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16, lineHeight: 1.5 }}>
          SatQuery AI evaluates three independent architectural configurations to test the research hypothesis:
          <i> Does query-driven routing with selective cross-model reasoning outperform static input-mode pipelines?</i>
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14 }}>
          {/* Config A */}
          <div
            style={{
              background: 'var(--bg-card)',
              border: routingConfig === 'CONFIG_A' ? '2px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
              borderRadius: 8,
              padding: 16,
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onClick={() => onSelectRoutingConfig('CONFIG_A')}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-main)' }}>Configuration A</span>
              <span className="mc-badge mc-badge-blue">Fixed Routing</span>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>
              Routes solely using input mode and declared image relationship without natural-language question interpretation.
            </div>
            <button
              type="button"
              className={`mc-nav-btn ${routingConfig === 'CONFIG_A' ? 'active' : ''}`}
              style={{ marginTop: 12, width: '100%', fontSize: 12 }}
            >
              {routingConfig === 'CONFIG_A' ? '✓ Currently Selected' : 'Select Config A'}
            </button>
          </div>

          {/* Config B */}
          <div
            style={{
              background: 'var(--bg-card)',
              border: routingConfig === 'CONFIG_B' ? '2px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
              borderRadius: 8,
              padding: 16,
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onClick={() => onSelectRoutingConfig('CONFIG_B')}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-main)' }}>Configuration B</span>
              <span className="mc-badge mc-badge-cyan">Query-Driven</span>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>
              Dynamically evaluates question semantics, input mode, image metadata, validation results, and model capabilities.
            </div>
            <button
              type="button"
              className={`mc-nav-btn ${routingConfig === 'CONFIG_B' ? 'active' : ''}`}
              style={{ marginTop: 12, width: '100%', fontSize: 12 }}
            >
              {routingConfig === 'CONFIG_B' ? '✓ Currently Selected' : 'Select Config B'}
            </button>
          </div>

          {/* Config C */}
          <div
            style={{
              background: 'var(--bg-card)',
              border: routingConfig === 'CONFIG_C' ? '2px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
              borderRadius: 8,
              padding: 16,
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onClick={() => onSelectRoutingConfig('CONFIG_C')}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-main)' }}>Configuration C</span>
              <span className="mc-badge mc-badge-green">Query + Cross-Model</span>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>
              Executes query-driven routing and selectively pairs ChangeStar change detection with GeoChat contextual scene explanations.
            </div>
            <button
              type="button"
              className={`mc-nav-btn ${routingConfig === 'CONFIG_C' ? 'active' : ''}`}
              style={{ marginTop: 12, width: '100%', fontSize: 12 }}
            >
              {routingConfig === 'CONFIG_C' ? '✓ Currently Selected (Default)' : 'Select Config C'}
            </button>
          </div>
        </div>
      </div>

      {/* 2. Specialist Model Registry & Diagnostics */}
      <ModelStatus />

      {/* 3. Automated Comparative Benchmark Suite */}
      <div className="mc-card">
        <div className="mc-card-header">
          <span className="mc-card-title">
            <span>⚡</span> EMPIRICAL BENCHMARK EVALUATION SUITE
          </span>
          <button
            className="mc-btn-primary"
            style={{ width: 'auto', padding: '8px 18px', fontSize: 12 }}
            onClick={handleRunBenchmark}
            disabled={benchmarking}
          >
            {benchmarking ? 'EXECUTING BENCHMARK SUITE...' : '⚡ RUN BENCHMARK SUITE'}
          </button>
        </div>

        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 14 }}>
          Evaluates 6 standardized benchmark cases across single-image VQA, referring expression grounding, bi-temporal change detection, and optical–SAR joint analysis.
        </p>

        {benchmarkResult && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
              <span className="mc-badge mc-badge-green">
                Task Acc: {(benchmarkResult.task_classification_accuracy * 100).toFixed(1)}%
              </span>
              <span className="mc-badge mc-badge-cyan">
                Routing Acc: {(benchmarkResult.routing_accuracy * 100).toFixed(1)}%
              </span>
              <span className="mc-badge mc-badge-blue">
                Avg Latency: {benchmarkResult.avg_routing_latency_ms.toFixed(2)} ms
              </span>
            </div>

            <table className="mc-table">
              <thead>
                <tr>
                  <th>Test Case</th>
                  <th>Query</th>
                  <th>Classified Task</th>
                  <th>Selected Specialist</th>
                  <th>Routing Latency</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {benchmarkResult.case_results.map((c: any) => (
                  <tr key={c.case_id}>
                    <td style={{ fontWeight: 600, color: 'var(--text-cyan)' }}>{c.case_id}</td>
                    <td>"{c.query}"</td>
                    <td><span className="mc-badge mc-badge-blue">{c.detected_task}</span></td>
                    <td>{c.selected_model || 'None (Rejected)'}</td>
                    <td>{c.latency_ms} ms</td>
                    <td>
                      <span className={`mc-badge ${c.routing_matched ? 'mc-badge-green' : 'mc-badge-rose'}`}>
                        {c.routing_matched ? 'PASSED' : 'FAILED'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {metrics && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10, marginTop: 14 }}>
            <div style={{ background: 'var(--bg-card)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Total Logged Trials</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-main)', marginTop: 2 }}>{metrics.total_experiments}</div>
            </div>
            <div style={{ background: 'var(--bg-card)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Pipeline Success Rate</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent-emerald)', marginTop: 2 }}>{(metrics.success_rate * 100).toFixed(1)}%</div>
            </div>
            <div style={{ background: 'var(--bg-card)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Avg Routing Overhead</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent-sky)', marginTop: 2 }}>{metrics.avg_routing_latency_ms.toFixed(2)} ms</div>
            </div>
            <div style={{ background: 'var(--bg-card)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Avg Total Latency</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-cyan)', marginTop: 2 }}>{metrics.avg_total_latency_ms.toFixed(1)} ms</div>
            </div>
          </div>
        )}
      </div>

      {/* 3b. Paper Table II: Comparative Evaluation Across Routing Configurations */}
      <div className="mc-card">
        <div className="mc-card-header">
          <span className="mc-card-title">
            <span>📊</span> TABLE II: ROUTING CONFIGURATIONS COMPARATIVE EVALUATION
          </span>
          <button
            className="mc-btn-primary"
            style={{ width: 'auto', padding: '8px 18px', fontSize: 12, background: 'var(--accent-blue)' }}
            onClick={handleRunTableII}
            disabled={tableIILoading}
          >
            {tableIILoading ? 'EVALUATING CONFIGURATIONS...' : '📊 RUN TABLE II ABLATION'}
          </button>
        </div>

        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 14 }}>
          Reproduces Section V-G Table II and evaluates the 5 quantitative metrics from Section V-F: Routing Accuracy (RA, Eq 11), Invalid-Input Rejection Rate (IRR, Eq 12), Execution Success Rate (ESR, Eq 13), End-to-End Reliability (EER, Eq 14), and Mean Latency (L_mean, Eq 15).
        </p>

        {tableIIResult ? (
          <div style={{ overflowX: 'auto' }}>
            <table className="mc-table">
              <thead>
                <tr>
                  <th>Configuration</th>
                  <th>Query Intent</th>
                  <th>Input Config</th>
                  <th>Compatibility</th>
                  <th>RA (Eq 11)</th>
                  <th>IRR (Eq 12)</th>
                  <th>ESR (Eq 13)</th>
                  <th>EER (Eq 14)</th>
                  <th>Latency (Eq 15)</th>
                  <th>Compat. Errors</th>
                </tr>
              </thead>
              <tbody>
                {tableIIResult.table_ii_metrics.map((row: any) => {
                  const isFull = row.configuration_key === 'satquery_ai';
                  return (
                    <tr
                      key={row.configuration_key}
                      style={{
                        background: isFull ? 'rgba(6, 182, 212, 0.08)' : 'transparent',
                        fontWeight: isFull ? 600 : 400
                      }}
                    >
                      <td style={{ color: isFull ? 'var(--text-cyan)' : 'var(--text-main)' }}>
                        {isFull && '★ '}
                        {row.configuration_name}
                      </td>
                      <td>{row.configuration_key === 'metadata_only' ? 'No' : 'Yes'}</td>
                      <td>{row.configuration_key === 'query_only' ? 'No' : 'Yes'}</td>
                      <td>
                        {row.configuration_key === 'query_only'
                          ? 'No'
                          : row.configuration_key === 'satquery_ai'
                          ? 'Yes'
                          : 'Limited'}
                      </td>
                      <td><b>{row.routing_accuracy_ra}%</b></td>
                      <td style={{ color: row.invalid_input_rejection_rate_irr === 100 ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                        <b>{row.invalid_input_rejection_rate_irr}%</b>
                      </td>
                      <td>{row.execution_success_rate_esr}%</td>
                      <td><b>{row.end_to_end_reliability_eer}%</b></td>
                      <td>{row.mean_latency_ms.toFixed(2)} ms</td>
                      <td>
                        <span className={`mc-badge ${row.failures_by_stage?.['3) Compatibility-validation failures'] === 0 ? 'mc-badge-green' : 'mc-badge-rose'}`}>
                          {row.failures_by_stage?.['3) Compatibility-validation failures'] ?? 0} errors
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-dim)', fontSize: 13, background: 'var(--bg-card)', borderRadius: 6 }}>
            Click "Run Table II Ablation" to compute the empirical comparison across Query-only, Metadata-only, Query+Input, and SatQuery AI configurations.
          </div>
        )}
      </div>

      {/* 4. Logged Experiments History */}
      <div className="mc-card">
        <div className="mc-card-header">
          <span className="mc-card-title">
            <span>📋</span> PERSISTED EXPERIMENT LOGS & TELEMETRY
          </span>
          <span className="mc-badge mc-badge-blue">{experiments.length} Records</span>
        </div>

        {experiments.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)', fontSize: 13 }}>
            No experiments logged yet. Execute analysis from the main workspace or run the benchmark suite.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="mc-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Query</th>
                  <th>Task</th>
                  <th>Modality</th>
                  <th>Specialist</th>
                  <th>Latency</th>
                  <th>Status</th>
                  <th>Report</th>
                </tr>
              </thead>
              <tbody>
                {experiments.map((exp) => (
                  <tr key={exp.request_id}>
                    <td style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                      {new Date(exp.timestamp).toLocaleTimeString()}
                    </td>
                    <td style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      "{exp.query}"
                    </td>
                    <td><span className="mc-badge mc-badge-blue">{exp.detected_task}</span></td>
                    <td>{exp.modality}</td>
                    <td><b>{exp.selected_model}</b></td>
                    <td>{exp.total_latency_ms.toFixed(1)} ms</td>
                    <td>
                      <span className={`mc-badge ${exp.status === 'success' ? 'mc-badge-green' : 'mc-badge-rose'}`}>
                        {exp.status.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <a
                        href={SatQueryApiService.getReportUrl(exp.request_id, 'html')}
                        target="_blank"
                        rel="noreferrer"
                        className="mc-badge mc-badge-cyan"
                        style={{ textDecoration: 'none' }}
                      >
                        HTML ↗
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
