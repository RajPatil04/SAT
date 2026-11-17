# backend/api/experiments.py
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from backend.research.experiment_logger import ExperimentLogger
from backend.research.metrics import ResearchMetrics
from backend.research.evaluation import ResearchEvaluator

router = APIRouter(prefix="/experiments", tags=["Research Experiments"])

@router.get("")
async def list_experiments(limit: int = 50):
    """
    Returns history of logged research experiments and routing evaluations.
    """
    return ExperimentLogger.get_recent_experiments(limit=limit)

@router.get("/metrics/summary")
async def get_metrics_summary():
    """
    Returns aggregate research performance metrics: routing overhead, success rate, and latencies.
    """
    return ResearchMetrics.calculate_system_metrics()

@router.post("/evaluate-benchmark")
async def run_benchmark_evaluation():
    """
    Runs automated evaluation across standardized benchmark query-asset suites.
    Returns task classification accuracy, routing accuracy, and routing latency.
    """
    return ResearchEvaluator.evaluate_benchmark_suite()

@router.get("/table-ii")
@router.post("/comparative-evaluation")
async def run_table_ii_comparative_evaluation():
    """
    Executes comparative evaluation across all 4 configurations defined in Table II of the paper:
    Query-only, Metadata-only, Query + Input, and SatQuery AI (Full Compatibility-Aware).
    Calculates RA, IRR, ESR, EER, and Mean Latency (Paper Section V-F).
    """
    return ResearchEvaluator.run_table_ii_evaluation()

@router.get("/{request_id}")
async def get_experiment_detail(request_id: str):
    """
    Returns detailed trace and execution telemetry for an experiment by request ID.
    """
    record = ExperimentLogger.get_experiment_by_request_id(request_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Experiment '{request_id}' not found.")
    return record
