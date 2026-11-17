# backend/api/reports.py
import os
import json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from backend.services.report_service import ReportService
from backend.research.experiment_logger import ExperimentLogger
from backend.config.settings import settings
from backend.router.schemas import (
    AnalysisResponse,
    RoutingDecision,
    CompatibilityResult,
    Evidence,
    ExecutionStep,
    ImageMetadata,
    TaskType,
    InputType,
    ModalityType
)

router = APIRouter(prefix="/report", tags=["Research Reports"])

@router.get("/{request_id}")
async def get_analysis_report(
    request_id: str,
    format: str = Query("html", enum=["html", "pdf"])
):
    """
    Downloads or renders a comprehensive research report for an analysis execution.
    """
    exp = ExperimentLogger.get_experiment_by_request_id(request_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"No experiment record found for request '{request_id}'.")

    # Reconstruct AnalysisResponse
    trace_steps = [
        ExecutionStep(**step_data) for step_data in exp.get("raw_trace", [])
    ]
    reasons = [r.strip() for r in (exp.get("routing_reasons") or "").split(";") if r.strip()]

    routing = RoutingDecision(
        selected_model_id=exp.get("selected_model"),
        selected_model_name=exp.get("selected_model"),
        detected_task=TaskType(exp.get("detected_task", "VQA")),
        detected_input_type=InputType(exp.get("input_type", "SINGLE_IMAGE")),
        detected_modality=ModalityType(exp.get("modality", "OPTICAL")),
        reasons=reasons,
        is_executable=exp.get("success", True)
    )

    compatibility = CompatibilityResult(
        is_compatible=exp.get("success", True),
        input_type=InputType(exp.get("input_type", "SINGLE_IMAGE")),
        modality=ModalityType(exp.get("modality", "OPTICAL"))
    )

    response = AnalysisResponse(
        request_id=exp["request_id"],
        query=exp["query"],
        task=routing.detected_task,
        input_type=routing.detected_input_type,
        modality=routing.detected_modality,
        status=exp["status"],
        answer=exp.get("answer") or "No answer recorded.",
        models_used=[exp["selected_model"]] if exp.get("selected_model") else [],
        evidence=Evidence(text="Grounded experiment evidence record."),
        confidence=exp.get("confidence"),
        routing=routing,
        metadata=[],
        compatibility=compatibility,
        execution_trace=trace_steps,
        total_duration_ms=exp.get("total_latency_ms", 0.0),
        timestamp=exp["timestamp"]
    )

    if format == "pdf":
        pdf_path = ReportService.generate_pdf_report(response)
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"report_{request_id}.pdf")

    html_path = ReportService.generate_html_report(response)
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)
