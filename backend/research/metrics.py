# backend/research/metrics.py
from typing import Dict, Any, List
from backend.database.database import SessionLocal
from backend.database.models import ExperimentRecordDB

class ResearchMetrics:
    @staticmethod
    def calculate_system_metrics() -> Dict[str, Any]:
        """
        Computes aggregate empirical performance metrics from logged experiments.
        """
        db = SessionLocal()
        try:
            records = db.query(ExperimentRecordDB).all()
            total_count = len(records)
            if total_count == 0:
                return {
                    "total_experiments": 0,
                    "success_rate": 0.0,
                    "avg_total_latency_ms": 0.0,
                    "avg_routing_latency_ms": 0.0,
                    "avg_model_latency_ms": 0.0,
                    "task_distribution": {},
                    "model_usage_distribution": {}
                }

            success_count = sum(1 for r in records if r.success)
            total_latencies = [r.total_latency_ms for r in records if r.total_latency_ms > 0]
            routing_latencies = [r.routing_latency_ms for r in records if r.routing_latency_ms > 0]
            model_latencies = [r.model_latency_ms for r in records if r.model_latency_ms > 0]

            task_counts: Dict[str, int] = {}
            model_counts: Dict[str, int] = {}
            for r in records:
                task_counts[r.detected_task] = task_counts.get(r.detected_task, 0) + 1
                model_name = r.selected_model or "None (Rejected/Halted)"
                model_counts[model_name] = model_counts.get(model_name, 0) + 1

            return {
                "total_experiments": total_count,
                "success_rate": round(success_count / total_count, 3),
                "avg_total_latency_ms": round(sum(total_latencies) / max(len(total_latencies), 1), 2),
                "avg_routing_latency_ms": round(sum(routing_latencies) / max(len(routing_latencies), 1), 2),
                "avg_model_latency_ms": round(sum(model_latencies) / max(len(model_latencies), 1), 2),
                "task_distribution": task_counts,
                "model_usage_distribution": model_counts
            }
        finally:
            db.close()
