# backend/router/model_registry.py
from typing import Dict, Any, List, Optional, Tuple
from backend.config.settings import settings
from backend.config.endpoint_config import CentralConfigManager
from backend.config.model_config import ModelSpec, REGISTERED_MODELS_CONFIG
from backend.router.schemas import (
    TaskType,
    InputType,
    ModalityType,
    ModelStatus,
    ModelInfoResponse
)

class ModelRegistry:
    @staticmethod
    def get_model_status(model_id: str) -> Tuple[ModelStatus, str]:
        """
        Determines model status from authoritative model_endpoints.yaml.
        Distinguishes between NOT_CONFIGURED, AVAILABLE, MOCK, and UNAVAILABLE.
        """
        cfg = REGISTERED_MODELS_CONFIG.get(model_id)
        if not cfg:
            return ModelStatus.UNAVAILABLE, f"Unknown model identifier '{model_id}'."

        service = CentralConfigManager.get_config().get_service(model_id)
        if service.is_configured():
            return ModelStatus.AVAILABLE, f"Remote endpoint configured via model_endpoints.yaml ({service.base_url}, {service.api_type})."

        # Check local weights for ChangeStar and CROMA
        if model_id == "changestar":
            from backend.models.changestar_adapter import ChangeStarAdapter
            if ChangeStarAdapter().is_configured():
                return ModelStatus.AVAILABLE, "ChangeStar weights available locally for in-process execution."
        elif model_id == "croma":
            from backend.models.croma_adapter import CROMAAdapter
            if CROMAAdapter().is_configured():
                return ModelStatus.AVAILABLE, "CROMA weights available locally for in-process execution."

        if settings.ENABLE_MOCK_FALLBACK_FOR_TESTS:
            return ModelStatus.MOCK, f"No remote endpoint specified for '{model_id}'; fallback simulation active (MOCK mode)."

        return ModelStatus.NOT_CONFIGURED, f"Model endpoint not configured. Set 'services.{model_id}.base_url' in backend/config/model_endpoints.yaml."

    @classmethod
    def list_models(cls) -> List[ModelInfoResponse]:
        results = []
        for model_id, cfg in REGISTERED_MODELS_CONFIG.items():
            status, msg = cls.get_model_status(model_id)
            service = CentralConfigManager.get_config().get_service(model_id)
            is_configured = service.is_configured()
            if not is_configured and model_id in ("changestar", "croma"):
                # Also consider local weights configured
                is_configured = (status == ModelStatus.AVAILABLE)

            results.append(
                ModelInfoResponse(
                    model_id=model_id,
                    display_name=cfg["display_name"],
                    version=cfg["version"],
                    description=cfg["description"],
                    tasks=[TaskType(t) for t in cfg["tasks"] if t in TaskType.__members__],
                    input_types=[InputType(i) for i in cfg["input_types"] if i in InputType.__members__],
                    modalities=[ModalityType(m) for m in cfg["modalities"] if m in ModalityType.__members__],
                    status=status,
                    status_message=msg,
                    endpoint_type=service.api_type if service.enabled else cfg.get("env_type_key", "gradio"),
                    endpoint_configured=is_configured,
                    supports_visual_grounding=cfg.get("supports_visual_grounding", False),
                    supports_change_maps=cfg.get("supports_change_maps", False),
                    supports_cross_attention_fusion=cfg.get("supports_cross_attention_fusion", False),
                    license=cfg.get("license", "Academic Research"),
                    paper_reference=cfg.get("paper_reference", "")
                )
            )
        return results

    @classmethod
    def get_model(cls, model_id: str) -> Optional[ModelInfoResponse]:
        for m in cls.list_models():
            if m.model_id == model_id:
                return m
        return None
