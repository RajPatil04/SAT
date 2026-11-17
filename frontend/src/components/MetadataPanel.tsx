// frontend/src/components/MetadataPanel.tsx
import React from 'react';
import { ImageMetadata, CompatibilityResult } from '../types/api';

interface MetadataPanelProps {
  metadata: ImageMetadata[];
  compatibility?: CompatibilityResult | null;
}

export const MetadataPanel: React.FC<MetadataPanelProps> = ({ metadata, compatibility }) => {
  if (!metadata || metadata.length === 0) return null;

  return (
    <div className="mc-card" style={{ marginBottom: 20 }}>
      <div className="mc-card-header">
        <span className="mc-card-title">
          <span>📊</span> RASTER & GEOSPATIAL METADATA INSPECTOR
        </span>
        {compatibility && (
          <span className={`mc-badge ${compatibility.is_compatible ? 'mc-badge-green' : 'mc-badge-rose'}`}>
            {compatibility.is_compatible ? 'SPATIOTEMPORALLY COMPATIBLE' : 'COMPATIBILITY NOTICE'}
          </span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14 }}>
        {metadata.map((m, idx) => (
          <div key={idx} style={{ background: 'var(--bg-card)', padding: 14, borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-cyan)' }}>{m.filename}</span>
              <span className="mc-badge mc-badge-blue">{m.format}</span>
            </div>

            <div style={{ fontSize: 12, color: 'var(--text-muted)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 12px' }}>
              <div><b>Dimensions:</b> {m.width} × {m.height} px</div>
              <div><b>Bands:</b> {m.channels} ({m.datatype})</div>
              <div><b>Modality:</b> <span className="mc-badge mc-badge-cyan">{m.detected_modality}</span></div>
              <div><b>GeoTIFF:</b> {m.is_geotiff ? 'Yes (Referenced)' : 'Standard Raster'}</div>
              <div><b>CRS:</b> {m.crs || 'Unreferenced'}</div>
              <div><b>Date:</b> {m.acquisition_date || 'Unspecified'}</div>
            </div>

            {m.resolution && (
              <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 8, borderTop: '1px solid var(--border-subtle)', paddingTop: 6 }}>
                Ground Sampling Distance: {m.resolution[0]}m / px
              </div>
            )}
          </div>
        ))}
      </div>

      {compatibility && compatibility.validation_messages.length > 0 && (
        <div style={{ marginTop: 14, background: 'rgba(2, 132, 199, 0.08)', padding: 10, borderRadius: 6, border: '1px solid rgba(2, 132, 199, 0.2)' }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--accent-sky)', textTransform: 'uppercase', marginBottom: 4 }}>
            Compatibility Engine Diagnostic Summary
          </div>
          <ul style={{ paddingLeft: 18, fontSize: 12, color: 'var(--text-main)', lineHeight: 1.5 }}>
            {compatibility.validation_messages.map((msg, i) => (
              <li key={i}>{msg}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
