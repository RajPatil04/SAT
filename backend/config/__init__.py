# backend/config/__init__.py
from backend.config.settings import settings
from backend.config.model_config import ModelConfig, ROUTING_WEIGHTS

__all__ = ["settings", "ModelConfig", "ROUTING_WEIGHTS"]
