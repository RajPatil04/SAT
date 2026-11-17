// frontend/src/components/ImageUploader.tsx
import React, { useRef, useState, useMemo, useEffect } from 'react';
import { ValidationResult } from '../types/api';

export type PrimaryMode = 'SINGLE_IMAGE' | 'DOUBLE_IMAGE';
export type ImageRelationship = 'BI_TEMPORAL' | 'OPTICAL_SAR' | 'UNKNOWN';

interface ImageUploaderProps {
  primaryMode: PrimaryMode;
  file1: File | null;
  file2: File | null;
  onFile1Change: (file: File | null) => void;
  onFile2Change: (file: File | null) => void;
  validationResult?: ValidationResult | null;
  isValidating?: boolean;
  relationship?: ImageRelationship;
  onRelationshipChange?: (rel: ImageRelationship) => void;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  primaryMode,
  file1,
  file2,
  onFile1Change,
  onFile2Change,
  validationResult,
  isValidating: _isValidating
}) => {
  const file1Ref = useRef<HTMLInputElement>(null);
  const file2Ref = useRef<HTMLInputElement>(null);

  const [dragActive1, setDragActive1] = useState(false);
  const [dragActive2, setDragActive2] = useState(false);

  const [dims1, setDims1] = useState<{ width: number; height: number } | null>(null);
  const [dims2, setDims2] = useState<{ width: number; height: number } | null>(null);

  const isDouble = primaryMode === 'DOUBLE_IMAGE';

  const preview1 = useMemo(() => {
    if (!file1) return null;
    const isArray = file1.name.endsWith('.npy') || file1.name.endsWith('.npz');
    if (isArray) return 'array';
    try {
      return URL.createObjectURL(file1);
    } catch {
      return null;
    }
  }, [file1]);

  const preview2 = useMemo(() => {
    if (!file2) return null;
    const isArray = file2.name.endsWith('.npy') || file2.name.endsWith('.npz');
    if (isArray) return 'array';
    try {
      return URL.createObjectURL(file2);
    } catch {
      return null;
    }
  }, [file2]);

  useEffect(() => {
    return () => {
      if (preview1 && preview1 !== 'array') URL.revokeObjectURL(preview1);
      if (preview2 && preview2 !== 'array') URL.revokeObjectURL(preview2);
    };
  }, [preview1, preview2]);

  useEffect(() => {
    if (!file1) {
      setDims1(null);
      return;
    }
    if (validationResult?.images?.[0]?.width) {
      setDims1({ width: validationResult.images[0].width, height: validationResult.images[0].height });
      return;
    }
    if (preview1 && preview1 !== 'array') {
      const img = new Image();
      img.onload = () => setDims1({ width: img.naturalWidth, height: img.naturalHeight });
      img.onerror = () => setDims1(null);
      img.src = preview1;
    }
  }, [file1, preview1, validationResult]);

  useEffect(() => {
    if (!file2) {
      setDims2(null);
      return;
    }
    if (validationResult?.images?.[1]?.width) {
      setDims2({ width: validationResult.images[1].width, height: validationResult.images[1].height });
      return;
    }
    if (preview2 && preview2 !== 'array') {
      const img = new Image();
      img.onload = () => setDims2({ width: img.naturalWidth, height: img.naturalHeight });
      img.onerror = () => setDims2(null);
      img.src = preview2;
    }
  }, [file2, preview2, validationResult]);

  const slot1Label = isDouble ? 'First Image' : 'Satellite Image';
  const slot1SupportingText = isDouble ? 'Upload the first satellite image' : 'GeoTIFF, TIFF, PNG, JPG, or NumPy (.npy)';

  const slot2Label = 'Second Image';
  const slot2SupportingText = 'Upload the second satellite image';

  const handleDrag = (e: React.DragEvent, setDrag: (active: boolean) => void) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDrag(true);
    } else if (e.type === 'dragleave') {
      setDrag(false);
    }
  };

  const handleDrop = (
    e: React.DragEvent,
    onFile: (f: File | null) => void,
    setDrag: (active: boolean) => void
  ) => {
    e.preventDefault();
    e.stopPropagation();
    setDrag(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Upload Slots: 1 for Single Image, 2 side-by-side for Double Image */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: isDouble ? '1fr 1fr' : '1fr',
        gap: 14
      }}>
        {/* Slot 1: First Image */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: '#0f172a' }}>{slot1Label}</span>
            {file1 && (
              <span className="sat-metadata-pill">
                {dims1 ? `${dims1.width}×${dims1.height} • ` : ''}{(file1.size / 1024).toFixed(1)} KB • {file1.name.split('.').pop()?.toUpperCase()}
              </span>
            )}
          </div>

          <input
            type="file"
            ref={file1Ref}
            style={{ display: 'none' }}
            accept=".tif,.tiff,.geotiff,.png,.jpg,.jpeg,.npy,.npz"
            onChange={(e) => onFile1Change(e.target.files?.[0] || null)}
          />

          {file1 ? (
            <div className="sat-upload-slot has-image">
              {preview1 === 'array' ? (
                <div className="sat-array-badge">
                  <span style={{ fontSize: 24 }}>📊</span>
                  <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--accent-blue)' }}>NumPy Array File</span>
                </div>
              ) : preview1 ? (
                <img
                  src={preview1}
                  alt="First Image Preview"
                  className="sat-preview-img"
                />
              ) : null}

              <button
                className="sat-remove-btn"
                type="button"
                title="Remove image"
                onClick={(e) => {
                  e.stopPropagation();
                  onFile1Change(null);
                }}
              >
                ✕
              </button>
              <div className="sat-file-name" title={file1.name}>
                {file1.name}
              </div>
            </div>
          ) : (
            <div
              className={`sat-upload-slot ${dragActive1 ? 'drag-active' : ''}`}
              onClick={() => file1Ref.current?.click()}
              onDragEnter={(e) => handleDrag(e, setDragActive1)}
              onDragOver={(e) => handleDrag(e, setDragActive1)}
              onDragLeave={(e) => handleDrag(e, setDragActive1)}
              onDrop={(e) => handleDrop(e, onFile1Change, setDragActive1)}
            >
              <div style={{ fontSize: 28, marginBottom: 6, color: 'var(--accent-blue)' }}>🛰️</div>
              <div style={{ fontSize: 12, fontWeight: 600, color: '#0f172a' }}>
                {slot1Label}
              </div>
              <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>
                {slot1SupportingText}
              </div>
            </div>
          )}

          {validationResult?.images?.[0]?.error && (
            <div style={{ marginTop: 6, padding: '6px 10px', fontSize: 11, color: '#b91c1c', background: '#fee2e2', borderRadius: 6, border: '1px solid #fca5a5', lineHeight: 1.4 }}>
              ⚠️ {validationResult.images[0].error}
            </div>
          )}
        </div>

        {/* Slot 2: Second Image (Double Image Mode Only) */}
        {isDouble && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: '#0f172a' }}>{slot2Label}</span>
              {file2 && (
                <span className="sat-metadata-pill">
                  {dims2 ? `${dims2.width}×${dims2.height} • ` : ''}{(file2.size / 1024).toFixed(1)} KB • {file2.name.split('.').pop()?.toUpperCase()}
                </span>
              )}
            </div>

            <input
              type="file"
              ref={file2Ref}
              style={{ display: 'none' }}
              accept=".tif,.tiff,.geotiff,.png,.jpg,.jpeg,.npy,.npz"
              onChange={(e) => onFile2Change(e.target.files?.[0] || null)}
            />

            {file2 ? (
              <div className="sat-upload-slot has-image">
                {preview2 === 'array' ? (
                  <div className="sat-array-badge">
                    <span style={{ fontSize: 24 }}>📊</span>
                    <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--accent-blue)' }}>NumPy Array File</span>
                  </div>
                ) : preview2 ? (
                  <img
                    src={preview2}
                    alt="Second Image Preview"
                    className="sat-preview-img"
                  />
                ) : null}

                <button
                  className="sat-remove-btn"
                  type="button"
                  title="Remove image"
                  onClick={(e) => {
                    e.stopPropagation();
                    onFile2Change(null);
                  }}
                >
                  ✕
                </button>
                <div className="sat-file-name" title={file2.name}>
                  {file2.name}
                </div>
              </div>
            ) : (
              <div
                className={`sat-upload-slot ${dragActive2 ? 'drag-active' : ''}`}
                onClick={() => file2Ref.current?.click()}
                onDragEnter={(e) => handleDrag(e, setDragActive2)}
                onDragOver={(e) => handleDrag(e, setDragActive2)}
                onDragLeave={(e) => handleDrag(e, setDragActive2)}
                onDrop={(e) => handleDrop(e, onFile2Change, setDragActive2)}
              >
                <div style={{ fontSize: 28, marginBottom: 6, color: 'var(--accent-blue)' }}>📡</div>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#0f172a' }}>
                  {slot2Label}
                </div>
                <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>
                  {slot2SupportingText}
                </div>
              </div>
            )}

            {validationResult?.images?.[1]?.error && (
              <div style={{ marginTop: 6, padding: '6px 10px', fontSize: 11, color: '#b91c1c', background: '#fee2e2', borderRadius: 6, border: '1px solid #fca5a5', lineHeight: 1.4 }}>
                ⚠️ {validationResult.images[1].error}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Validation Advisory Alert */}
      {validationResult && (validationResult.warnings.length > 0 || validationResult.blocking_errors.length > 0) && (
        <div className="sat-validation-advisory">
          <div className="sat-validation-advisory-title">
            <span>⚠️</span> Validation Advisory
          </div>
          {validationResult.blocking_errors.map((err, idx) => (
            <div key={`err-${idx}`} className="sat-validation-advisory-item">• {err}</div>
          ))}
          {validationResult.warnings.map((w, idx) => (
            <div key={`warn-${idx}`} className="sat-validation-advisory-item">• {w}</div>
          ))}
        </div>
      )}
    </div>
  );
};
