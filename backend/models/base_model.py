# backend/models/base_model.py
import abc
import time
from typing import Dict, Any, List, Optional, Tuple

class BaseModelAdapter(abc.ABC):
    def __init__(self, model_id: str, display_name: str):
        self.model_id = model_id
        self.display_name = display_name

    @abc.abstractmethod
    async def predict(
        self,
        query: str,
        file_paths: List[str],
        task: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executes model inference and returns a standardized result payload.
        Expected return dictionary:
        {
            "answer": str,
            "confidence": Optional[float],
            "evidence": {
                "text": Optional[str],
                "regions": List[Dict],
                "boxes": List[Dict],
                "overlay_url": Optional[str],
                "change_mask_url": Optional[str]
            },
            "is_simulated": bool,
            "model_latency_ms": float,
            "raw_output": Any
        }
        """
        pass

    @abc.abstractmethod
    async def health_check(self) -> Tuple[bool, str]:
        """
        Checks connectivity to the model endpoint.
        Returns: (is_healthy, status_message)
        """
        pass

    @abc.abstractmethod
    def is_configured(self) -> bool:
        """
        Returns True if the required environment variables (e.g. API URL) are set.
        """
        pass
