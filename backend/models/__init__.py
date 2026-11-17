# backend/models/__init__.py
from backend.models.base_model import BaseModelAdapter
from backend.models.geochat_adapter import GeoChatAdapter
from backend.models.changestar_adapter import ChangeStarAdapter
from backend.models.change_model_adapter import ChangeModelAdapter
from backend.models.croma_adapter import CROMAAdapter
from backend.models.grounding_adapter import GroundingAdapter
from backend.models.mock_adapter import MockSpecialistAdapter

MODEL_ADAPTERS = {
    "geochat-7b": GeoChatAdapter,
    "changestar": ChangeStarAdapter,
    "croma": CROMAAdapter,
    "grounding-specialist": GroundingAdapter
}

def get_adapter(model_id: str) -> BaseModelAdapter:
    from backend.config.settings import settings
    adapter_cls = MODEL_ADAPTERS.get(model_id)
    if not adapter_cls:
        if settings.ENABLE_MOCK_FALLBACK_FOR_TESTS:
            return MockSpecialistAdapter(model_id, model_id, "General Specialist")
        raise KeyError(f"Specialist model adapter for '{model_id}' is not registered.")
    return adapter_cls()

__all__ = [
    "BaseModelAdapter",
    "GeoChatAdapter",
    "ChangeStarAdapter",
    "ChangeModelAdapter",
    "CROMAAdapter",
    "GroundingAdapter",
    "MockSpecialistAdapter",
    "MODEL_ADAPTERS",
    "get_adapter"
]
