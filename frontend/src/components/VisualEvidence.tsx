// frontend/src/components/VisualEvidence.tsx
import React from 'react';
import { Evidence } from '../types/api';
import { SatQueryApiService } from '../services/api';

interface VisualEvidenceProps {
  evidence?: Evidence | null;
  baseImages: File[];
}

export const VisualEvidence: React.FC<VisualEvidenceProps> = ({ evidence, baseImages }) => {
  const hasOverlay = Boolean(evidence?.overlay_url || evidence?.change_mask_url);

  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
        Visual Grounding & Spectral Evidence
      </div>

      <div className="mc-media-grid">
        {/* Input Observation 1 */}
        {baseImages[0] && (
          <div className="mc-media-frame">
            <img src={URL.createObjectURL(baseImages[0])} alt="Input 1" />
            <div className="mc-media-tag">Observation T1 / Primary Optical</div>
          </div>
        )}

        {/* Input Observation 2 */}
        {baseImages[1] && (
          <div className="mc-media-frame">
            <img src={URL.createObjectURL(baseImages[1])} alt="Input 2" />
            <div className="mc-media-tag">Observation T2 / Secondary Modality</div>
          </div>
        )}

        {/* Visual Overlay / Change Mask (If provided) */}
        {hasOverlay ? (
          <div className="mc-media-frame" style={{ border: '2px solid var(--accent-cyan)' }}>
            <img
              src={SatQueryApiService.resolveMediaUrl(evidence?.overlay_url || evidence?.change_mask_url) || ''}
              alt="Model Visual Evidence"
            />
            <div className="mc-media-tag" style={{ background: 'var(--accent-cyan)', color: '#070b13', fontWeight: 600 }}>
              Specialist Visual Overlay / Grounding Mask
            </div>
          </div>
        ) : (
          <div
            className="mc-media-frame"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 24,
              textAlign: 'center',
              background: 'rgba(15, 23, 42, 0.4)'
            }}
          >
            <div style={{ fontSize: 13, color: 'var(--text-dim)' }}>
              <div style={{ fontSize: 24, marginBottom: 8 }}>🛰️</div>
              <b>Visual evidence not provided by selected model.</b>
              <div style={{ fontSize: 11, marginTop: 4 }}>
                Selected specialist produced textual and regional grounding.
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bounding Boxes List if available */}
      {evidence?.boxes && evidence.boxes.length > 0 && (
        <div style={{ background: 'var(--bg-card)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)', marginBottom: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-cyan)', marginBottom: 6 }}>
            REFERRING EXPRESSION GROUNDING BOXES
          </div>
          {evidence.boxes.map((b, idx) => (
            <div key={idx} style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              • <b>{b.label}:</b> [{b.box_2d.map(c => c.toFixed(3)).join(', ')}]
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
