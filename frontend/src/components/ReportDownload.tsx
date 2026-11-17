// frontend/src/components/ReportDownload.tsx
import React from 'react';
import { SatQueryApiService } from '../services/api';

interface ReportDownloadProps {
  requestId: string;
}

export const ReportDownload: React.FC<ReportDownloadProps> = ({ requestId }) => {
  return (
    <div className="mc-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px' }}>
      <div>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-cyan)' }}>
          📄 EXPORT PUBLICATION-GRADE RESEARCH REPORT
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
          Complete execution telemetry, routing rationale, metadata, and grounded findings.
        </div>
      </div>

      <div style={{ display: 'flex', gap: 10 }}>
        <a
          href={SatQueryApiService.getReportUrl(requestId, 'html')}
          target="_blank"
          rel="noreferrer"
          className="mc-badge mc-badge-blue"
          style={{ textDecoration: 'none', padding: '8px 14px', fontSize: 12 }}
        >
          View HTML Report ↗
        </a>
        <a
          href={SatQueryApiService.getReportUrl(requestId, 'pdf')}
          download={`report_${requestId}.pdf`}
          className="mc-badge mc-badge-cyan"
          style={{ textDecoration: 'none', padding: '8px 14px', fontSize: 12 }}
        >
          Download PDF Report ↓
        </a>
      </div>
    </div>
  );
};
