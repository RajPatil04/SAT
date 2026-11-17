# backend/research/experiment_logger.py
import json
import logging
from typing import Dict, Any, Optional, List
from backend.config.settings import settings
from backend.database.database import SessionLocal
from backend.database.models import ExperimentRecordDB
from backend.router.schemas import AnalysisResponse

logger = logging.getLogger("satquery.experiment_logger")

class ExperimentLogger:
    @staticmethod
    def log_analysis(response: AnalysisResponse, model_latency_ms: float = 0.0):
        """
        Persists analysis execution metadata, routing decisions, and timings to SQLite.
        Does not store raw imagery in the database.
        """
        if not settings.EXPERIMENT_LOGGING:
            return

        db = SessionLocal()
        try:
            record = ExperimentRecordDB(
                request_id=response.request_id,
                query=response.query,
                input_type=response.input_type.value,
                modality=response.modality.value,
                detected_task=response.task.value,
                selected_model=response.routing.selected_model_name,
                routing_reasons="; ".join(response.routing.reasons),
                routing_latency_ms=round(response.total_duration_ms - model_latency_ms, 2),
                model_latency_ms=round(model_latency_ms, 2),
                total_latency_ms=round(response.total_duration_ms, 2),
                status=response.status,
                success=(response.status == "success"),
                answer=response.answer[:1000] if response.answer else None,
                confidence=response.confidence,
                compatibility_summary=f"Compatible: {response.compatibility.is_compatible}",
                metadata_summary=f"Images: {len(response.metadata)}",
                raw_trace_json=json.dumps([step.model_dump() for step in response.execution_trace])
            )
            db.add(record)
            db.commit()
            logger.info(f"Experiment logged successfully for request_id: {response.request_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to log experiment record: {str(e)}")
        finally:
            db.close()

    @staticmethod
    def get_recent_experiments(limit: int = 50) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            records = db.query(ExperimentRecordDB).order_by(ExperimentRecordDB.id.desc()).limit(limit).all()
            return [
                {
                    "id": r.id,
                    "request_id": r.request_id,
                    "timestamp": r.timestamp.isoformat(),
                    "query": r.query,
                    "input_type": r.input_type,
                    "modality": r.modality,
                    "detected_task": r.detected_task,
                    "selected_model": r.selected_model,
                    "total_latency_ms": r.total_latency_ms,
                    "model_latency_ms": r.model_latency_ms,
                    "routing_latency_ms": r.routing_latency_ms,
                    "status": r.status,
                    "success": r.success,
                    "answer": r.answer,
                    "confidence": r.confidence
                }
                for r in records
            ]
        finally:
            db.close()

    @staticmethod
    def get_experiment_by_request_id(request_id: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            r = db.query(ExperimentRecordDB).filter(ExperimentRecordDB.request_id == request_id).first()
            if not r:
                return None
            return {
                "id": r.id,
                "request_id": r.request_id,
                "timestamp": r.timestamp.isoformat(),
                "query": r.query,
                "input_type": r.input_type,
                "modality": r.modality,
                "detected_task": r.detected_task,
                "selected_model": r.selected_model,
                "routing_reasons": r.routing_reasons,
                "total_latency_ms": r.total_latency_ms,
                "model_latency_ms": r.model_latency_ms,
                "routing_latency_ms": r.routing_latency_ms,
                "status": r.status,
                "success": r.success,
                "answer": r.answer,
                "confidence": r.confidence,
                "raw_trace": json.loads(r.raw_trace_json) if r.raw_trace_json else []
            }
        finally:
            db.close()
