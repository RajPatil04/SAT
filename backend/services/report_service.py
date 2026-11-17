# backend/services/report_service.py
import os
import json
from typing import Dict, Any, Optional
from backend.config.settings import settings
from backend.router.schemas import AnalysisResponse

class ReportService:
    @staticmethod
    def generate_html_report(response: AnalysisResponse) -> str:
        """
        Generates a publication-grade HTML research report for the analysis.
        """
        trace_rows = "".join([
            f"<tr><td>{s.step}</td><td>{s.component}</td><td><span class='badge {s.status}'>{s.status}</span></td><td>{s.duration_ms:.1f} ms</td><td>{s.message}</td></tr>"
            for s in response.execution_trace
        ])

        meta_cards = "".join([
            f"<div class='meta-box'><h4>{m.filename}</h4><p>Format: {m.format} | Size: {m.width}x{m.height} | Bands: {m.channels} | Modality: {m.detected_modality.value}</p></div>"
            for m in response.metadata
        ])

        candidate_scores_rows = "".join([
            f"<tr><td>{c.display_name}</td><td><b>{c.total_score:.3f}</b></td><td>{c.task_match_score}</td><td>{c.input_type_match_score}</td><td>{c.modality_match_score}</td><td>{c.availability_status.value}</td></tr>"
            for c in response.routing.candidate_scores
        ])

        confidence_str = f"{response.confidence:.2f}" if response.confidence is not None else "Confidence not provided by model"
        router_conf_str = f"{response.router_confidence:.2f}" if response.router_confidence is not None else "N/A"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SatQuery AI Analysis Report - {response.request_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 40px; }}
        .container {{ max-width: 960px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 32px; border: 1px solid #334155; }}
        h1 {{ color: #38bdf8; margin-top: 0; border-bottom: 2px solid #0284c7; padding-bottom: 12px; }}
        h2 {{ color: #7dd3fc; margin-top: 28px; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
        .header-meta {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .badge.completed {{ background: #065f46; color: #34d399; }}
        .badge.failed {{ background: #7f1d1d; color: #f87171; }}
        .answer-box {{ background: #090d16; border-left: 4px solid #38bdf8; padding: 18px; border-radius: 6px; font-size: 16px; line-height: 1.6; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }}
        th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #334155; }}
        th {{ background: #0f172a; color: #94a3b8; }}
        .meta-box {{ background: #0f172a; padding: 12px; border-radius: 6px; margin-bottom: 8px; }}
        .meta-box h4 {{ margin: 0 0 4px 0; color: #38bdf8; }}
        .meta-box p {{ margin: 0; color: #94a3b8; font-size: 13px; }}
        .footer {{ margin-top: 40px; font-size: 12px; color: #64748b; text-align: center; border-top: 1px solid #334155; padding-top: 16px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>SATQUERY AI - Research Analysis Report</h1>
        <p style="color: #94a3b8;">An Agentic Vision-Language Framework for Query-Driven Multimodal Remote-Sensing Analysis</p>

        <div class="header-meta">
            <div><b>Request ID:</b> {response.request_id}</div>
            <div><b>Timestamp:</b> {response.timestamp}</div>
            <div><b>Total Processing Time:</b> {response.total_duration_ms:.1f} ms</div>
            <div><b>Detected Task:</b> {response.task.value}</div>
            <div><b>Input Type:</b> {response.input_type.value}</div>
            <div><b>Modality:</b> {response.modality.value}</div>
        </div>

        <h2>User Query</h2>
        <div style="font-size: 18px; color: #e2e8f0; font-weight: 500; margin: 12px 0;">"{response.query}"</div>

        <h2>Specialist Model Response</h2>
        <div class="answer-box">
            <b>Selected Model:</b> {response.routing.selected_model_name or "None"}<br>
            <b>Model Confidence:</b> {confidence_str}<br>
            <b>Router Confidence:</b> {router_conf_str}<br><br>
            <b>Grounded Findings:</b><br>
            {response.answer}
        </div>

        <h2>Evidence & Grounding</h2>
        <p><b>Summary:</b> {response.evidence.text or "No textual evidence summary."}</p>
        {"<p><b>Optical Feature Summary:</b> " + response.evidence.optical_feature_summary + "</p>" if response.evidence.optical_feature_summary else ""}
        {"<p><b>SAR Feature Summary:</b> " + response.evidence.sar_feature_summary + "</p>" if response.evidence.sar_feature_summary else ""}

        <h2>Input Raster Metadata</h2>
        {meta_cards}

        <h2>Model Routing Evaluation</h2>
        <p><b>Routing Rationale:</b></p>
        <ul>
            {"".join(f"<li>{r}</li>" for r in response.routing.reasons)}
        </ul>
        <table>
            <thead>
                <tr><th>Model Candidate</th><th>Total Score</th><th>Task Match</th><th>Input Match</th><th>Modality Match</th><th>Availability</th></tr>
            </thead>
            <tbody>
                {candidate_scores_rows}
            </tbody>
        </table>

        <h2>Execution Trace</h2>
        <table>
            <thead>
                <tr><th>Step</th><th>Component</th><th>Status</th><th>Duration</th><th>Action</th></tr>
            </thead>
            <tbody>
                {trace_rows}
            </tbody>
        </table>

        <div class="footer">
            Generated autonomously by SatQuery AI Research Framework.
        </div>
    </div>
</body>
</html>
"""
        filename = f"report_{response.request_id}.html"
        file_path = os.path.join(settings.REPORTS_DIR, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return file_path

    @staticmethod
    def generate_pdf_report(response: AnalysisResponse) -> str:
        """
        Generates a downloadable PDF report using ReportLab.
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        filename = f"report_{response.request_id}.pdf"
        file_path = os.path.join(settings.REPORTS_DIR, filename)

        doc = SimpleDocTemplate(file_path, pagesize=letter)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#0284c7'),
            spaceAfter=10
        )
        body_style = styles['Normal']

        elements = []
        elements.append(Paragraph("SATQUERY AI - RESEARCH ANALYSIS REPORT", title_style))
        elements.append(Paragraph(f"<b>Request ID:</b> {response.request_id} | <b>Timestamp:</b> {response.timestamp}", body_style))
        elements.append(Paragraph(f"<b>Query:</b> \"{response.query}\"", body_style))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph(f"<b>Detected Task:</b> {response.task.value} | <b>Input:</b> {response.input_type.value} | <b>Modality:</b> {response.modality.value}", body_style))
        elements.append(Paragraph(f"<b>Selected Specialist Model:</b> {response.routing.selected_model_name or 'None'}", body_style))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("<b>Answer & Empirical Findings:</b>", styles['Heading3']))
        elements.append(Paragraph(response.answer, body_style))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("<b>Routing Trace:</b>", styles['Heading3']))
        for reason in response.routing.reasons:
            elements.append(Paragraph(f"• {reason}", body_style))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("<b>Execution Trace:</b>", styles['Heading3']))
        trace_data = [["Step", "Component", "Status", "Duration (ms)", "Action"]]
        for s in response.execution_trace:
            trace_data.append([str(s.step), s.component, s.status, f"{s.duration_ms:.1f}", s.message[:50]])

        t = Table(trace_data, colWidths=[35, 110, 65, 75, 230])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        elements.append(t)

        doc.build(elements)
        return file_path
