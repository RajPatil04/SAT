// frontend/src/services/api.ts
// IMPORTANT: ZERO MODEL URLs ALLOWED HERE.
// All interactions are securely proxied through the SatQuery FastAPI backend.

import {
  AnalysisResponse,
  CompatibilityResult,
  ValidationResult,
  ModelInfoResponse,
  SystemStatusResponse,
  ExperimentSummary,
  SystemMetrics
} from '../types/api';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class SatQueryApiService {
  static getBaseUrl(): string {
    return API_BASE;
  }

  static async checkHealth(): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE}/api/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return res.json();
  }

  static async getSystemStatus(): Promise<SystemStatusResponse> {
    const res = await fetch(`${API_BASE}/api/system-status`);
    if (!res.ok) throw new Error(`System status failed: ${res.statusText}`);
    return res.json();
  }

  static async getModels(): Promise<ModelInfoResponse[]> {
    const res = await fetch(`${API_BASE}/api/models`);
    if (!res.ok) throw new Error(`Fetch models failed: ${res.statusText}`);
    return res.json();
  }

  static async getCapabilities(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/models/capabilities`);
    if (!res.ok) throw new Error(`Fetch capabilities failed: ${res.statusText}`);
    return res.json();
  }

  static async analyze(formData: FormData): Promise<AnalysisResponse> {
    const res = await fetch(`${API_BASE}/api/analyze`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail?.errors ? err.detail.errors.join('; ') : (err.detail || 'Analysis request failed'));
    }
    return res.json();
  }

  static async validate(formData: FormData): Promise<ValidationResult> {
    const res = await fetch(`${API_BASE}/api/validate`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Validation request failed');
    }
    return res.json();
  }

  static async getExperiments(): Promise<ExperimentSummary[]> {
    const res = await fetch(`${API_BASE}/api/experiments`);
    if (!res.ok) throw new Error(`Fetch experiments failed: ${res.statusText}`);
    return res.json();
  }

  static async getMetrics(): Promise<SystemMetrics> {
    const res = await fetch(`${API_BASE}/api/experiments/metrics/summary`);
    if (!res.ok) throw new Error(`Fetch metrics failed: ${res.statusText}`);
    return res.json();
  }

  static async runBenchmark(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/experiments/evaluate-benchmark`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error(`Benchmark evaluation failed: ${res.statusText}`);
    return res.json();
  }

  static async runTableIIEvaluation(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/experiments/table-ii`);
    if (!res.ok) throw new Error(`Table II evaluation failed: ${res.statusText}`);
    return res.json();
  }

  static getReportUrl(requestId: string, format: 'html' | 'pdf' = 'html'): string {
    return `${API_BASE}/api/report/${requestId}?format=${format}`;
  }

  static resolveMediaUrl(relativeUrl?: string | null): string | null {
    if (!relativeUrl) return null;
    if (relativeUrl.startsWith('http')) return relativeUrl;
    return `${API_BASE}${relativeUrl.startsWith('/') ? '' : '/'}${relativeUrl}`;
  }
}
