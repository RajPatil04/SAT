// frontend/src/components/ResultPanel.tsx
import React, { useState, useMemo, useEffect } from 'react';
import { AnalysisResponse } from '../types/api';
import { SatQueryApiService } from '../services/api';

interface ResultPanelProps {
  response: AnalysisResponse;
  baseImages: File[];
  onRetry?: () => void;
}

export const ResultPanel: React.FC<ResultPanelProps> = ({ response, baseImages, onRetry }) => {
  const [imgLoadError, setImgLoadError] = useState(false);
  const [showVisualEvidence, setShowVisualEvidence] = useState(false);

  const isRejected = response.status === 'rejected_incompatible';
  const isUnavailable = response.status === 'unavailable';
  const isError = response.status === 'error';

  // Object URLs for uploaded observations
  const imgUrl1 = useMemo(() => {
    if (!baseImages[0]) return null;
    if (baseImages[0].name.endsWith('.npy') || baseImages[0].name.endsWith('.npz')) return null;
    try {
      return URL.createObjectURL(baseImages[0]);
    } catch {
      return null;
    }
  }, [baseImages]);

  const imgUrl2 = useMemo(() => {
    if (!baseImages[1]) return null;
    if (baseImages[1].name.endsWith('.npy') || baseImages[1].name.endsWith('.npz')) return null;
    try {
      return URL.createObjectURL(baseImages[1]);
    } catch {
      return null;
    }
  }, [baseImages]);

  useEffect(() => {
    return () => {
      if (imgUrl1) URL.revokeObjectURL(imgUrl1);
      if (imgUrl2) URL.revokeObjectURL(imgUrl2);
    };
  }, [imgUrl1, imgUrl2]);

  // Only genuine models that actually executed inference are reported as executed
  const executedModels = (response.models_used && response.models_used.length > 0)
    ? response.models_used
    : (response.routing?.selected_model_name ? [response.routing.selected_model_name] : ['Specialist Model']);

  const executedModelsText = executedModels.join(', ');

  const overlayUrl = response.evidence?.overlay_url || response.evidence?.change_mask_url;
  const hasVisualMap = Boolean(overlayUrl && overlayUrl.trim());

  // Format bold markdown and clean bullet points for answer body
  const renderFormattedAnswer = (text: string) => {
    if (!text || !text.trim()) {
      return (
        <span style={{ color: 'var(--text-dim)', fontStyle: 'italic' }}>
          No natural-language interpretation was returned by the model.
        </span>
      );
    }

    const paragraphs = text.split('\n\n');
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {paragraphs.map((para, pIdx) => {
          const lines = para.split('\n');
          return (
            <div key={pIdx} style={{ lineHeight: 1.65 }}>
              {lines.map((line, lIdx) => {
                const trimmed = line.trim();
                const isBullet = trimmed.startsWith('•') || trimmed.startsWith('* ') || trimmed.startsWith('- ');
                const cleanLine = isBullet ? trimmed.replace(/^[•*-]\s*/, '') : line;
                const parts = cleanLine.split(/(\*\*.*?\*\*)/g);

                return (
                  <div
                    key={lIdx}
                    style={{
                      marginTop: isBullet ? 6 : 0,
                      display: isBullet ? 'flex' : 'block',
                      alignItems: 'baseline',
                      paddingLeft: isBullet ? 2 : 0
                    }}
                  >
                    {isBullet && (
                      <span style={{ color: '#0284c7', fontWeight: 800, marginRight: 8, fontSize: 16 }}>
                        •
                      </span>
                    )}
                    <span style={{ flex: 1, color: '#1e293b' }}>
                      {parts.map((part, partIdx) => {
                        if (part.startsWith('**') && part.endsWith('**')) {
                          return <strong key={partIdx} style={{ fontWeight: 700, color: '#0f172a' }}>{part.slice(2, -2)}</strong>;
                        }
                        return part;
                      })}
                    </span>
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    );
  };

  // If rejected, unavailable, or failed: show clear user-friendly error card with retry
  if (isRejected || isUnavailable || isError) {
    return (
      <div className="sat-error-card">
        <div className="sat-error-icon">
          {isRejected ? '⚠️' : '✕'}
        </div>
        <div style={{ flex: 1 }}>
          <div className="sat-error-title">
            {isRejected
              ? 'Input Incompatible with Requested Task'
              : isUnavailable
              ? 'Specialist Service Unavailable'
              : 'Analysis Failed'}
          </div>
          <div className="sat-error-message">
            {response.answer || 'The selected specialist model could not complete analysis for the provided input.'}
          </div>
          {response.limitations && response.limitations.length > 0 && (
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
              {response.limitations.map((lim, idx) => (
                <div key={idx}>• {lim}</div>
              ))}
            </div>
          )}
          {onRetry && (
            <button className="sat-retry-btn" type="button" onClick={onRetry}>
              🔄 Adjust & Retry Analysis
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="sat-result-card">
      {/* 1. Header: Heading + Model Badges */}
      <div className="sat-result-header">
        <div className="sat-result-heading">
          <span>🎯</span> Analysis Result
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <button
            type="button"
            className="sat-badge-pill sat-badge-cyan"
            style={{ cursor: 'pointer' }}
            onClick={() => {
              const blob = new Blob([JSON.stringify(response, null, 2)], { type: 'application/json' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `satquery_report_${response.request_id}.json`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            title="Download complete structured execution record as JSON"
          >
            <span>📥</span> Export Report (.JSON)
          </button>
          <span className="sat-badge-pill sat-badge-green">
            <span>🚀</span> Executed: {executedModelsText}
          </span>
          <span className="sat-badge-pill sat-badge-blue">
            {response.task_type || response.task}
          </span>
          {response.confidence !== null && response.confidence !== undefined ? (
            <span className="sat-badge-pill sat-badge-green" title="Calibrated posterior confidence">
              <span>🎯</span> {Math.round(response.confidence * 100)}% Confidence
            </span>
          ) : (
            <span className="sat-badge-pill sat-badge-gray" title="Empirical mask or unsupervised representation without calibrated posterior probability">
              <span>📊</span> Empirical Output (Uncalibrated)
            </span>
          )}
        </div>
      </div>

      {/* 2. Actual Grounded Natural-Language Answer */}
      <div className="sat-answer-body">
        {renderFormattedAnswer(response.answer)}
      </div>

      {/* Visual Map / Overlay toggle (if change mask or overlay exists) */}
      {hasVisualMap && (
        <div style={{ marginTop: 14 }}>
          <button
            type="button"
            className="sat-link-btn"
            style={{ fontSize: 12, display: 'inline-flex', alignItems: 'center', gap: 6, color: '#0284c7', fontWeight: 600 }}
            onClick={() => setShowVisualEvidence(!showVisualEvidence)}
          >
            <span>{showVisualEvidence ? '▲ Hide Visual Change Map' : '▼ View Visual Change Map & Previews'}</span>
          </button>

          {showVisualEvidence && (
            <div className="sat-evidence-section" style={{ marginTop: 10 }}>
              <div className="sat-evidence-grid">
                {imgUrl1 && (
                  <div className="sat-evidence-item">
                    <div className="sat-evidence-img-wrap">
                      <img src={imgUrl1} alt="Observation T1 (Pre-Change)" />
                    </div>
                    <div className="sat-evidence-label">
                      <span>Observation T1</span>
                    </div>
                  </div>
                )}
                {imgUrl2 && (
                  <div className="sat-evidence-item">
                    <div className="sat-evidence-img-wrap">
                      <img src={imgUrl2} alt="Observation T2 (Post-Change)" />
                    </div>
                    <div className="sat-evidence-label">
                      <span>Observation T2</span>
                    </div>
                  </div>
                )}
                <div className="sat-evidence-item highlight-map">
                  <div className="sat-evidence-img-wrap">
                    {!imgLoadError ? (
                      <img
                        src={SatQueryApiService.resolveMediaUrl(overlayUrl) || ''}
                        alt="Generated Change Map"
                        onError={() => setImgLoadError(true)}
                      />
                    ) : (
                      <div className="sat-evidence-failed-msg">
                        ⚠️ Unable to render change map overlay.
                      </div>
                    )}
                  </div>
                  <div className="sat-evidence-label">
                    <span>
                      Generated Change Map ({executedModelsText})
                      {response.evidence?.change_percentage !== undefined && response.evidence?.change_percentage !== null && (
                        <> • {response.evidence.change_percentage}%</>
                      )}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Limitations Warning (if any) */}
      {response.limitations && response.limitations.length > 0 && (
        <div className="sat-limitations-box">
          <span style={{ fontSize: 16 }}>⚠️</span>
          <div>
            <b>Scientific Advisory:</b> {response.limitations.join(' • ')}
          </div>
        </div>
      )}
    </div>
  );
};
