// frontend/src/pages/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { ImageUploader, PrimaryMode } from '../components/ImageUploader';
import { QueryInput } from '../components/QueryInput';
import { ResultPanel } from '../components/ResultPanel';
import { AdvancedDetailsPanel } from '../components/AdvancedDetailsPanel';
import { SatQueryApiService } from '../services/api';
import { AnalysisResponse, ValidationResult } from '../types/api';

interface DashboardProps {
  routingConfig?: string;
  onOpenResearch?: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  routingConfig = 'CONFIG_C',
  onOpenResearch
}) => {
  // Section 1 & 8: Explicit State Variables
  const [primaryMode, setPrimaryMode] = useState<PrimaryMode>('SINGLE_IMAGE');
  const [file1, setFile1] = useState<File | null>(null);
  const [file2, setFile2] = useState<File | null>(null);
  const [query, setQuery] = useState('What objects and land-cover types are visible?');

  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  // Core Analysis Lifecycle States (Section 8)
  const [analysisStatus, setAnalysisStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Section 3: Dedicated Advanced Details State (Hidden by default)
  const [showAdvancedDetails, setShowAdvancedDetails] = useState<boolean>(false);

  // Switch default queries when primary mode changes
  const handleSelectPrimaryMode = (newMode: PrimaryMode) => {
    setPrimaryMode(newMode);
    if (newMode === 'SINGLE_IMAGE') {
      setQuery('What objects and land-cover types are visible?');
    } else {
      setQuery('What changes occurred between these two images?');
    }
  };

  // Pre-flight validation whenever files, mode, or query change
  useEffect(() => {
    let isCancelled = false;

    async function runPreflightValidation() {
      if (!file1 && !file2) {
        setValidationResult(null);
        return;
      }

      setIsValidating(true);
      const fd = new FormData();
      if (file1) fd.append('images', file1);
      if (primaryMode === 'DOUBLE_IMAGE' && file2) fd.append('images', file2);
      fd.append('input_mode', primaryMode);
      fd.append('question', query || 'Validate');

      try {
        const val = await SatQueryApiService.validate(fd);
        if (!isCancelled) {
          setValidationResult(val);
        }
      } catch {
        // Silent validation failure handling
      } finally {
        if (!isCancelled) setIsValidating(false);
      }
    }

    runPreflightValidation();

    return () => {
      isCancelled = true;
    };
  }, [file1, file2, primaryMode, query]);

  const canSubmit = Boolean(
    file1 &&
    (primaryMode === 'SINGLE_IMAGE' || (primaryMode === 'DOUBLE_IMAGE' && file2)) &&
    query.trim()
  );

  const handleAnalyze = async () => {
    if (!file1) return;
    setAnalysisStatus('loading');
    setAnalysisError(null);
    setShowAdvancedDetails(false);

    const formData = new FormData();
    formData.append('images', file1);
    if (primaryMode === 'DOUBLE_IMAGE' && file2) {
      formData.append('images', file2);
    }
    formData.append('question', query);
    formData.append('input_mode', primaryMode);
    formData.append('routing_config', routingConfig);

    try {
      const res = await SatQueryApiService.analyze(formData);
      setAnalysisResult(res);
      setAnalysisStatus('success');
      if (res.validation) {
        setValidationResult(res.validation);
      }
    } catch (e: any) {
      setAnalysisError(e.message || 'Analysis execution error occurred.');
      setAnalysisStatus('error');
    }
  };

  const currentFiles = [file1, file2].filter(Boolean) as File[];

  return (
    <div className="sat-workspace-container">
      {/* Floating Orbital Satellite illustration in the background */}
      <img src="/satellite_clean.png" alt="Orbiting Satellite" className="sat-orbiting-satellite" />

      {/* 1. Main Screen: Mode Selector + Two-Column Balanced Input Card */}
      <div className="sat-card">
        {/* Mode Selector Tabs (Single Image vs Double Image) */}
        <div className="sat-mode-switch">
          <button
            type="button"
            className={`sat-mode-btn ${primaryMode === 'SINGLE_IMAGE' ? 'active' : ''}`}
            onClick={() => handleSelectPrimaryMode('SINGLE_IMAGE')}
          >
            <span className="sat-mode-icon">⚡</span>
            <span>Single Image</span>
          </button>
          <button
            type="button"
            className={`sat-mode-btn ${primaryMode === 'DOUBLE_IMAGE' ? 'active' : ''}`}
            onClick={() => handleSelectPrimaryMode('DOUBLE_IMAGE')}
          >
            <span className="sat-mode-icon">👥</span>
            <span>Double Image</span>
          </button>
        </div>

        {/* Balanced Two-Column Layout on Desktop: Uploads (Left) + Question & Action (Right) */}
        <div className="sat-input-grid">
          <div className="sat-grid-col">
            <ImageUploader
              primaryMode={primaryMode}
              file1={file1}
              file2={file2}
              onFile1Change={setFile1}
              onFile2Change={setFile2}
              validationResult={validationResult}
              isValidating={isValidating}
            />
          </div>

          <div className="sat-grid-col">
            <QueryInput
              primaryMode={primaryMode}
              query={query}
              onQueryChange={setQuery}
              onAnalyze={handleAnalyze}
              isLoading={analysisStatus === 'loading'}
              canSubmit={canSubmit}
            />
          </div>
        </div>
      </div>

      {/* 2. Before Analysis: Simple Instruction Banner (Section 2) */}
      {analysisStatus === 'idle' && !analysisResult && (
        <div className="sat-instruction-banner">
          <div className="sat-instruction-icon">🛰️</div>
          <div className="sat-instruction-text">
            Upload your satellite image, ask a question, and analyze.
          </div>
          {onOpenResearch && (
            <button
              type="button"
              className="sat-link-btn"
              onClick={onOpenResearch}
            >
              Need system benchmarks or model comparisons? View Research & Diagnostics ↗
            </button>
          )}
        </div>
      )}

      {/* 3. While Processing: Clear Loading Indicator (Section 2) */}
      {analysisStatus === 'loading' && (
        <div className="sat-loading-card">
          <div className="mc-spinner sat-large-spinner" />
          <div className="sat-loading-title">Analyzing your satellite imagery...</div>
          <div className="sat-loading-subtitle">
            Validating imagery, executing specialist model, and synthesizing evidence...
          </div>
        </div>
      )}

      {/* 4. Analysis Failure: Friendly Error Card with Retry (Section 2) */}
      {analysisStatus === 'error' && analysisError && (
        <div className="sat-error-card">
          <div className="sat-error-icon">⚠️</div>
          <div style={{ flex: 1 }}>
            <div className="sat-error-title">Analysis Failed</div>
            <div className="sat-error-message">{analysisError}</div>
            <button className="sat-retry-btn" type="button" onClick={handleAnalyze}>
              🔄 Retry Analysis
            </button>
          </div>
        </div>
      )}

      {/* 5. Actual Analysis Result Card (Section 2 & 5) */}
      {analysisStatus === 'success' && analysisResult && (
        <div>
          <ResultPanel
            response={analysisResult}
            baseImages={currentFiles}
            onRetry={handleAnalyze}
          />

          {/* 6. Dedicated Compact Button for Advanced Details (Section 3) */}
          <div style={{ textAlign: 'center', marginTop: 18 }}>
            <button
              className="sat-advanced-btn"
              type="button"
              onClick={() => setShowAdvancedDetails(!showAdvancedDetails)}
            >
              <span>{showAdvancedDetails ? '▲' : '▼'}</span>
              <span>{showAdvancedDetails ? 'Hide Advanced Details' : 'Advanced Details'}</span>
              <span className="sat-badge-subtle">
                {analysisResult.selected_models?.[0] || 'Technical Telemetry'}
              </span>
            </button>
          </div>

          {/* 7. Collapsible Advanced Details Panel (Section 3) */}
          {showAdvancedDetails && (
            <div style={{ marginTop: 16 }}>
              <AdvancedDetailsPanel response={analysisResult} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
