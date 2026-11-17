// frontend/src/components/EvidencePanel.tsx
import React from 'react';
import { Evidence } from '../types/api';
import { VisualEvidence } from './VisualEvidence';

interface EvidencePanelProps {
  evidence?: Evidence | null;
  baseImages: File[];
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ evidence, baseImages }) => {
  if (!evidence) return null;

  return (
    <div className="mc-card" style={{ marginBottom: 20 }}>
      <div className="mc-card-header">
        <span className="mc-card-title">
          <span>🔬</span> EMPIRICAL EVIDENCE & MULTIMODAL GROUNDING
        </span>
      </div>

      <VisualEvidence evidence={evidence} baseImages={baseImages} />

      {/* Multimodal Features Breakdown */}
      {(evidence.optical_feature_summary || evidence.sar_feature_summary) && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
          {evidence.optical_feature_summary && (
            <div style={{ background: 'var(--bg-card)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--accent-sky)', textTransform: 'uppercase', marginBottom: 4 }}>
                Optical Spectral Features
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-main)', lineHeight: 1.5 }}>
                {evidence.optical_feature_summary}
              </div>
            </div>
          )}

          {evidence.sar_feature_summary && (
            <div style={{ background: 'var(--bg-card)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--accent-cyan)', textTransform: 'uppercase', marginBottom: 4 }}>
                SAR Backscatter & Polarization Features
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-main)', lineHeight: 1.5 }}>
                {evidence.sar_feature_summary}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Detected Regions */}
      {evidence.regions && evidence.regions.length > 0 && (
        <div style={{ background: 'var(--bg-card)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-cyan)', textTransform: 'uppercase', marginBottom: 6 }}>
            Quantified Modification Sectors & Regional Changes
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 8 }}>
            {evidence.regions.map((reg, i) => (
              <div key={i} style={{ background: 'var(--bg-panel)', padding: '8px 12px', borderRadius: 4, border: '1px solid var(--border-subtle)', fontSize: 12 }}>
                <span style={{ color: 'var(--accent-rose)', fontWeight: 600 }}>• </span>
                <b>{reg.description || `Sector ${reg.region_id}`}:</b> {reg.change_intensity ? `Intensity: ${reg.change_intensity}` : ''}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
