# backend/api/models.py
from typing import List
from fastapi import APIRouter, HTTPException
from backend.router.schemas import ModelInfoResponse, TaskType, InputType, ModalityType
from backend.router.model_registry import ModelRegistry
from backend.config.model_config import ROUTING_WEIGHTS

router = APIRouter(prefix="/models", tags=["Models & Capabilities"])

@router.get("", response_model=List[ModelInfoResponse])
async def list_registered_models():
    """
    Returns the list of all registered remote-sensing specialist models and their capabilities.
    """
    return ModelRegistry.list_models()

@router.get("/status")
async def get_models_status():
    """
    Returns live health, loaded weights, hardware device, and readiness for specialist models.
    """
    from backend.models import get_adapter
    statuses = {}
    for model_id in ["geochat-7b", "changestar", "croma", "grounding-specialist"]:
        adapter = get_adapter(model_id)
        is_healthy, msg = await adapter.health_check()
        statuses[model_id] = {
            "name": adapter.display_name,
            "configured": adapter.is_configured(),
            "healthy": is_healthy,
            "status_message": msg
        }
    return statuses

@router.get("/capabilities")
async def get_system_capabilities():
    """
    Returns supported tasks, input structures, modalities, and routing formulation parameters.
    """
    return {
        "supported_tasks": [t.value for t in TaskType if t != TaskType.UNKNOWN],
        "supported_input_types": [i.value for i in InputType if i != InputType.UNKNOWN],
        "supported_modalities": [m.value for m in ModalityType if m != ModalityType.UNKNOWN],
        "routing_formulation": {
            "title": "Proposed Query-Driven Model Routing Formulation",
            "formula": "Score(q, m) = w1*TaskMatch + w2*InputTypeMatch + w3*ModalityMatch + w4*CapabilityMatch + w5*Compatibility + w6*Availability",
            "weights": ROUTING_WEIGHTS
        }
    }

@router.get("/{model_id}", response_model=ModelInfoResponse)
async def get_model_details(model_id: str):
    """
    Retrieves detailed capability specifications for a specific model identifier.
    """
    model = ModelRegistry.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model with id '{model_id}' is not registered.")
    return model
