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
        mode_clean = (mode or "").lower()
        q_clean = (query or "").lower()

        # Bi-temporal change detection
        if "bi_temporal" in mode_clean or "pair" in mode_clean or "change" in q_clean or "temporal" in q_clean or "between" in q_clean:
            return "Bi-temporal Change Analysis", "ChangeStar", self.changestar

        # Optical + SAR cross-modal
        if "optical_sar" in mode_clean or "sar" in mode_clean or "radar" in q_clean or "cross" in q_clean or "croma" in q_clean:
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
