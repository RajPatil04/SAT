# backend/router/capability_matcher.py
from typing import Dict, Any, List
from backend.config.model_config import ROUTING_WEIGHTS, REGISTERED_MODELS_CONFIG
from backend.router.schemas import (
    TaskType,
    InputType,
    ModalityType,
    ModelStatus,
    ModelCandidateScore,
    CompatibilityResult
)
from backend.router.model_registry import ModelRegistry

class CapabilityMatcher:
    @staticmethod
    def score_model(
        model_id: str,
        task: TaskType,
        input_type: InputType,
        modality: ModalityType,
        compatibility: CompatibilityResult
    ) -> ModelCandidateScore:
        """
        Calculates the candidate model score according to the
        Proposed Query-Driven Model Routing Formulation:
        Score(q, m) = w1 * TaskMatch + w2 * InputTypeMatch + w3 * ModalityMatch 
                    + w4 * CapabilityMatch + w5 * Compatibility + w6 * Availability
        """
        cfg = REGISTERED_MODELS_CONFIG.get(model_id, {})
        display_name = cfg.get("display_name", model_id)
        supported_tasks = cfg.get("tasks", [])
        supported_inputs = cfg.get("input_types", [])
        supported_modalities = cfg.get("modalities", [])

        # 1. Task Match
        if task.value in supported_tasks:
            task_score = 1.0
        elif task == TaskType.CAPTIONING and "VQA" in supported_tasks:
            task_score = 0.75
        elif task == TaskType.SCENE_ANALYSIS and "VQA" in supported_tasks:
            task_score = 0.75
        elif task == TaskType.OBJECT_ANALYSIS and ("VQA" in supported_tasks or "GROUNDING" in supported_tasks):
            task_score = 0.80
        elif task == TaskType.CHANGE_VQA and "CHANGE_DETECTION" in supported_tasks:
            task_score = 0.85
        else:
            task_score = 0.0

        # 2. Input Type Match
        if input_type.value in supported_inputs:
            input_score = 1.0
        else:
            input_score = 0.0

        # 3. Modality Match
        if modality.value in supported_modalities or "UNKNOWN" in supported_modalities:
            modality_score = 1.0
        elif modality == ModalityType.OPTICAL and "MULTISPECTRAL" in supported_modalities:
            modality_score = 0.9
        elif modality == ModalityType.MULTISPECTRAL and "OPTICAL" in supported_modalities:
            modality_score = 0.8
        else:
            modality_score = 0.0

        # 4. Capability Match (Specific specialized features)
        capability_score = 0.8
        if task == TaskType.GROUNDING:
            capability_score = 1.0 if cfg.get("supports_visual_grounding", False) else 0.0
        elif task in (TaskType.CHANGE_DETECTION, TaskType.CHANGE_VQA):
            capability_score = 1.0 if cfg.get("supports_change_maps", False) else 0.2
        elif task == TaskType.OPTICAL_SAR_ANALYSIS:
            capability_score = 1.0 if cfg.get("supports_cross_attention_fusion", False) else 0.0

        # 5. Compatibility Score
        compatibility_score = 1.0 if compatibility.is_compatible else 0.1

        # 6. Availability Score
        status, status_msg = ModelRegistry.get_model_status(model_id)
        if status == ModelStatus.AVAILABLE:
            availability_score = 1.0
        elif status == ModelStatus.MOCK:
            availability_score = 0.85  # Usable for simulation/evaluation
        elif status == ModelStatus.NOT_CONFIGURED:
            availability_score = 0.0
        else:
            availability_score = 0.0

        # Compute Weighted Score
        w = ROUTING_WEIGHTS
        total_score = (
            w["w1_task_match"] * task_score +
            w["w2_input_type_match"] * input_score +
            w["w3_modality_match"] * modality_score +
            w["w4_capability_match"] * capability_score +
            w["w5_compatibility"] * compatibility_score +
            w["w6_availability"] * availability_score
        )

        return ModelCandidateScore(
            model_id=model_id,
            display_name=display_name,
            total_score=round(total_score, 4),
            task_match_score=round(task_score, 3),
            input_type_match_score=round(input_score, 3),
            modality_match_score=round(modality_score, 3),
            capability_match_score=round(capability_score, 3),
            compatibility_score=round(compatibility_score, 3),
            availability_score=round(availability_score, 3),
            availability_status=status,
            status_message=status_msg
        )

    @classmethod
    def rank_candidates(
        cls,
        task: TaskType,
        input_type: InputType,
        modality: ModalityType,
        compatibility: CompatibilityResult
    ) -> List[ModelCandidateScore]:
        candidates = []
        for model_id in REGISTERED_MODELS_CONFIG.keys():
            score = cls.score_model(model_id, task, input_type, modality, compatibility)
            candidates.append(score)
        # Sort descending by total score
        candidates.sort(key=lambda c: c.total_score, reverse=True)
        return candidates
