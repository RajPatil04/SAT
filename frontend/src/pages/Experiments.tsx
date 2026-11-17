// frontend/src/pages/Experiments.tsx
import React, { useEffect, useState } from 'react';
import { ExperimentSummary, SystemMetrics } from '../types/api';
import { SatQueryApiService } from '../services/api';

export const Experiments: React.FC = () => {
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [benchmarkResult, setBenchmarkResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [benchmarking, setBenchmarking] = useState(false);

  const loadData = async () => {
    try {
      const [expList, met] = await Promise.all([
        SatQueryApiService.getExperiments(),
        SatQueryApiService.getMetrics()
      ]);
      setExperiments(expList);
      setMetrics(met);
    } catch (e) {
      console.error('Failed to load experiments:', e);
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
      console.error('Benchmark failed:', e);
    } finally {
      setBenchmarking(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-main)', letterSpacing: '0.04em' }}>
            RESEARCH EXPERIMENT LOGS & BENCHMARK SUITE
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
            Empirical logging of queries, routing latency overhead, specialist selection, and benchmark accuracy.
          </p>
        </div>

        <button
          className="mc-btn-primary"
          style={{ width: 'auto', padding: '10px 18px', fontSize: 12 }}
          onClick={handleRunBenchmark}
          disabled={benchmarking}
        >
          {benchmarking ? 'RUNNING BENCHMARKS...' : '⚡ RUN AUTOMATED BENCHMARK SUITE'}
        </button>
      </div>

      {/* Aggregate Metrics Cards */}
      {metrics && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14, marginBottom: 20 }}>
          <div className="mc-card" style={{ padding: 14 }}>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Logged Trials</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-cyan)', marginTop: 4 }}>
              {metrics.total_experiments}
            </div>
          </div>

          <div className="mc-card" style={{ padding: 14 }}>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Pipeline Success Rate</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--accent-emerald)', marginTop: 4 }}>
              {(metrics.success_rate * 100).toFixed(1)}%
            </div>
          </div>

          <div className="mc-card" style={{ padding: 14 }}>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Avg Routing Overhead</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--accent-sky)', marginTop: 4 }}>
              {metrics.avg_routing_latency_ms.toFixed(2)} ms
            </div>
          </div>

          <div className="mc-card" style={{ padding: 14 }}>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Avg Total Latency</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-main)', marginTop: 4 }}>
              {metrics.avg_total_latency_ms.toFixed(1)} ms
            </div>
          </div>
        </div>
      )}

      {/* Benchmark Evaluation Results */}
      {benchmarkResult && (
        <div className="mc-card" style={{ marginBottom: 20, border: '1px solid var(--accent-cyan)' }}>
          <div className="mc-card-header">
            <span className="mc-card-title">
              <span>⚡</span> BENCHMARK SUITE EVALUATION RESULTS
            </span>
            <div style={{ display: 'flex', gap: 10 }}>
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

      {/* Logged Experiments History */}
      <div className="mc-card">
        <div className="mc-card-header">
          <span className="mc-card-title">
            <span>📋</span> TRIAL TELEMETRY & PERSISTED EXPERIMENTS
          </span>
          <span className="mc-badge mc-badge-blue">{experiments.length} Records</span>
        </div>

        {experiments.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 30, color: 'var(--text-muted)' }}>
            No experiments logged yet. Run an analysis from the Mission Control dashboard or trigger the benchmark suite.
          </div>
        ) : (
          <table className="mc-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Query</th>
                <th>Task</th>
                <th>Modality</th>
                <th>Specialist Model</th>
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
                  <td style={{ maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    "{exp.query}"
                  </td>
                  <td><span className="mc-badge mc-badge-blue">{exp.detected_task}</span></td>
                  <td><span className="mc-badge mc-badge-cyan">{exp.modality}</span></td>
                  <td>{exp.selected_model || 'None'}</td>
                  <td>{exp.total_latency_ms.toFixed(1)} ms</td>
                  <td>
                    <span className={`mc-badge ${exp.success ? 'mc-badge-green' : 'mc-badge-amber'}`}>
                      {exp.status.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <a
                      href={SatQueryApiService.getReportUrl(exp.request_id, 'html')}
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: 'var(--accent-sky)', textDecoration: 'none', fontSize: 12 }}
                    >
                      Report ↗
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
