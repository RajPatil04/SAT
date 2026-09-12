"""
Agentic Router for SatQuery AI.
Analyzes input modalities, temporal dimensions, and natural language queries
to dynamically select and orchestrate the appropriate specialist model.
"""
from typing import Dict, Any, Tuple
from models.geochat import GeoChatModel
from models.changestar import ChangeStarModel
from models.croma import CROMAModel

class SatQueryAgentRouter:
    def __init__(self):
        self.geochat = GeoChatModel()
        self.changestar = ChangeStarModel()
        self.croma = CROMAModel()

    def route(self, mode: str, query: str = "", metadata: Dict[str, Any] = None) -> Tuple[str, str, Any]:
        """
        Determines the appropriate specialist model based on input mode and query keywords.
        Returns (detected_task, selected_model_name, model_instance)
        """
        mode_clean = (mode or "").lower().strip()
        q_clean = (query or "").lower().strip()

        # 1. Strict mode enforcement (when mode is explicitly provided by UI/client)
        if mode_clean in ["single_image", "single"]:
            return "Single-image Understanding", "GeoChat", self.geochat

        if mode_clean in ["bi_temporal", "temporal", "bitemporal", "pair"]:
            return "Bi-temporal Change Analysis", "ChangeStar", self.changestar

        if mode_clean in ["optical_sar", "sar", "cross_modal", "croma"]:
            return "Cross-modal Analysis", "CROMA", self.croma

        # 2. Heuristic fallback when mode is generic or auto
        if any(w in q_clean for w in ["change", "temporal", "between", "delta", "before", "after", "expansion"]):
            return "Bi-temporal Change Analysis", "ChangeStar", self.changestar

        if any(w in q_clean for w in ["sar", "radar", "cross", "croma", "cloud", "microwave"]):
            return "Cross-modal Analysis", "CROMA", self.croma

        # Default: Single Image VQA / Grounding / Captioning
        return "Single-image Understanding", "GeoChat", self.geochat

    def execute_pipeline(self, mode: str, query: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Executes full agentic pipeline with observable intermediate stages."""
        task, model_name, model_inst = self.route(mode, query, metadata)
        prediction = model_inst.predict(metadata or {}, query)
        return {
            "routed_task": task,
            "selected_model": model_name,
            "prediction": prediction
        }
