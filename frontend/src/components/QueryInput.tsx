// frontend/src/components/QueryInput.tsx
import React from 'react';
import { PrimaryMode } from './ImageUploader';

export type RoutingConfigType = 'CONFIG_A' | 'CONFIG_B' | 'CONFIG_C';

interface QueryInputProps {
  primaryMode: PrimaryMode;
  query: string;
  onQueryChange: (q: string) => void;
  onAnalyze: () => void;
  isLoading: boolean;
  canSubmit: boolean;
}

export const QueryInput: React.FC<QueryInputProps> = ({
  primaryMode,
  query,
  onQueryChange,
  onAnalyze,
  isLoading,
  canSubmit
}) => {
  const singleImageExamples = [
    "What objects and land-cover types are visible?",
    "Describe the important features in this image.",
    "Identify visible roads, buildings, vegetation, and water bodies."
  ];

  const doubleImageExamples = [
    "What changes occurred between these two images?",
    "Where have new buildings appeared?",
    "Has vegetation or water coverage changed?",
    "Compare the structural information visible in these images"
  ];

  const activeExamples = primaryMode === 'SINGLE_IMAGE' ? singleImageExamples : doubleImageExamples;

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      if (canSubmit && !isLoading) onAnalyze();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'space-between' }}>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
          <label style={{ fontSize: 11.5, fontWeight: 700, color: '#1e3a8a', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            NATURAL-LANGUAGE QUESTION
          </label>
          <span style={{ fontSize: 11, color: '#64748b' }}>
            Ctrl+Enter to run
          </span>
        </div>

        <textarea
          className="sat-query-textarea"
          rows={3}
          placeholder={primaryMode === 'SINGLE_IMAGE'
            ? "Ask about land-cover, objects, features, or scene overview in this image..."
            : "What changes occurred between these two images?"}
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={handleKeyDown}
        />

        <div style={{ marginTop: 10 }}>
          <div style={{ fontSize: 12, fontWeight: 500, color: '#475569', marginBottom: 6 }}>
            Quick suggestions:
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-start' }}>
            {activeExamples.map((ex, idx) => (
              <button
                key={idx}
                type="button"
                className="sat-example-pill"
                onClick={() => onQueryChange(ex)}
              >
                <span style={{ marginRight: 6 }}>💬</span> "{ex}"
              </button>
            ))}
          </div>
        </div>
      </div>

      <button
        className="sat-analyze-btn"
        type="button"
        onClick={onAnalyze}
        disabled={!canSubmit || isLoading}
      >
        {isLoading ? (
          <>
            <span className="mc-spinner" style={{ width: 18, height: 18, borderWidth: 2 }} />
            <span>Analyzing your satellite imagery...</span>
          </>
        ) : (
          <>
            <span style={{ fontSize: 16 }}>⚡</span>
            <span>Analyze Imagery</span>
          </>
        )}
      </button>
    </div>
  );
};
