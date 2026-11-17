# backend/config/model_config.py
"""
Central Model Registry Configuration & Proposed Query-Driven Routing Formulation Weights.

Scientific Note:
The routing scoring formula is documented as:
"Proposed Query-Driven Model Routing Formulation"
Score(q, m) = w1 * TaskMatch + w2 * InputTypeMatch + w3 * ModalityMatch 
            + w4 * CapabilityMatch + w5 * Compatibility + w6 * Availability
"""

from typing import Dict, Any, List
from pydantic import BaseModel, ConfigDict

# Configurable Weights for the Proposed Query-Driven Model Routing Formulation
ROUTING_WEIGHTS = {
    "w1_task_match": 0.25,
    "w2_input_type_match": 0.20,
    "w3_modality_match": 0.15,
    "w4_capability_match": 0.15,
    "w5_compatibility": 0.15,
    "w6_availability": 0.10,
}

class ModelSpec(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: str
    display_name: str
    version: str
    description: str
    tasks: List[str]
    input_types: List[str]
    modalities: List[str]
    adapter_class: str
    env_url_key: str
    env_type_key: str
    env_endpoint_key: str
    supports_visual_grounding: bool = False
    supports_change_maps: bool = False
    supports_cross_attention_fusion: bool = False
    license: str = "Research / Academic Use"
    paper_reference: str = ""

REGISTERED_MODELS_CONFIG: Dict[str, Dict[str, Any]] = {
    "geochat-7b": {
        "model_id": "geochat-7b",
        "display_name": "GeoChat-7B",
        "version": "1.0",
        "description": "Grounded Large Vision-Language Model tailored for multimodal remote sensing and earth observation.",
        "tasks": ["VQA", "CAPTIONING", "SCENE_ANALYSIS", "OBJECT_ANALYSIS", "GROUNDING"],
        "input_types": ["SINGLE_IMAGE"],
        "modalities": ["OPTICAL", "MULTISPECTRAL", "UNKNOWN"],
        "adapter_class": "GeoChatAdapter",
        "env_url_key": "GEOCHAT_API_URL",
        "env_type_key": "GEOCHAT_API_TYPE",
        "env_endpoint_key": "GEOCHAT_API_ENDPOINT",
        "supports_visual_grounding": True,
        "supports_change_maps": False,
        "supports_cross_attention_fusion": False,
        "license": "Apache 2.0 / Academic Research",
        "paper_reference": "Kuckreja et al., 'GeoChat: Grounded Large Vision-Language Model for Remote Sensing', CVPR 2024"
    },
    "changestar": {
        "model_id": "changestar",
        "display_name": "ChangeStar",
        "version": "1.0",
        "description": "Bi-temporal remote sensing change detection specialist for dense feature comparison and change quantification.",
        "tasks": ["CHANGE_DETECTION", "CHANGE_VQA"],
        "input_types": ["BI_TEMPORAL"],
        "modalities": ["OPTICAL", "MULTISPECTRAL"],
        "adapter_class": "ChangeModelAdapter",
        "env_url_key": "CHANGE_MODEL_API_URL",
        "env_type_key": "CHANGE_MODEL_API_TYPE",
        "env_endpoint_key": "CHANGE_MODEL_API_ENDPOINT",
        "supports_visual_grounding": False,
        "supports_change_maps": True,
        "supports_cross_attention_fusion": False,
        "license": "MIT / Academic Research",
        "paper_reference": "Zheng et al., 'ChangeStar: A General Framework for Bi-temporal Earth Observation', ICLR 2021"
    },
    "croma": {
        "model_id": "croma",
        "display_name": "CROMA (Optical-SAR Specialist)",
        "version": "1.0",
        "description": "Cross-modal contrastive and cross-attention specialist for combined Sentinel-1 (SAR) and Sentinel-2 (Optical) inference.",
        "tasks": ["OPTICAL_SAR_ANALYSIS"],
        "input_types": ["OPTICAL_SAR_PAIR"],
        "modalities": ["OPTICAL_SAR"],
        "adapter_class": "CROMAAdapter",
        "env_url_key": "CROMA_API_URL",
        "env_type_key": "CROMA_API_TYPE",
        "env_endpoint_key": "CROMA_API_ENDPOINT",
        "supports_visual_grounding": False,
        "supports_change_maps": False,
        "supports_cross_attention_fusion": True,
        "license": "MIT / Academic Research",
        "paper_reference": "Anthony et al., 'CROMA: Cross-Modal Contrastive and Self-Supervised Learning for Optical and SAR', NeurIPS 2023"
    },
    "grounding-specialist": {
        "model_id": "grounding-specialist",
        "display_name": "RS-GroundingSpecialist",
        "version": "1.0",
        "description": "Remote-sensing spatial grounding specialist capable of generating bounding boxes and spatial masks.",
        "tasks": ["GROUNDING", "OBJECT_ANALYSIS"],
        "input_types": ["SINGLE_IMAGE"],
        "modalities": ["OPTICAL", "MULTISPECTRAL"],
        "adapter_class": "GroundingAdapter",
        "env_url_key": "GROUNDING_API_URL",
        "env_type_key": "GROUNDING_API_TYPE",
        "env_endpoint_key": "GROUNDING_API_ENDPOINT",
        "supports_visual_grounding": True,
        "supports_change_maps": False,
        "supports_cross_attention_fusion": False,
        "license": "MIT / Academic Research",
        "paper_reference": "Vision-Language Grounding for Earth Observation Specialist Architecture"
    }
}

class ModelConfig:
    @staticmethod
    def get_registered_models() -> Dict[str, Dict[str, Any]]:
        return REGISTERED_MODELS_CONFIG

    @staticmethod
    def get_model_spec(model_id: str) -> Dict[str, Any]:
        return REGISTERED_MODELS_CONFIG.get(model_id)

    @staticmethod
    def get_routing_weights() -> Dict[str, float]:
        return ROUTING_WEIGHTS
