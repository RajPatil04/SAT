# backend/router/routing_rules.py
from typing import Dict, Any, List, Optional, Tuple
from backend.router.schemas import (
    TaskType,
    InputType,
    ModalityType,
    CompatibilityResult
)

class RoutingRules:
    @staticmethod
    def validate_task_input_consistency(
        task: TaskType,
        input_type: InputType,
        num_images: int,
        modality: ModalityType,
        query: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Applies rigorous remote-sensing domain constraints to verify that the
        user's query intent and uploaded assets are physically and mathematically consistent.
        """
        # Rule 1: Change detection or change VQA requires at least two observations.
        if task in (TaskType.CHANGE_DETECTION, TaskType.CHANGE_VQA):
            if num_images < 2 or input_type == InputType.SINGLE_IMAGE:
                return (
                    False,
                    "Change analysis requires at least two temporal observations. "
                    "Please provide the images to compare (e.g. before/after dates)."
                )

        # Rule 2: Multi-temporal analysis requires >= 3 images.
        if task == TaskType.MULTI_TEMPORAL_ANALYSIS:
            if num_images < 3:
                return (
                    False,
                    f"Multi-temporal analysis requires at least 3 temporal epochs, but {num_images} provided."
                )

        # Rule 3: Optical + SAR joint analysis requires both modalities.
        if task == TaskType.OPTICAL_SAR_ANALYSIS:
            if input_type != InputType.OPTICAL_SAR_PAIR and num_images < 2:
                return (
                    False,
                    "Optical-SAR analysis requires paired multimodal imagery (one Optical observation and one SAR acquisition). "
                    "Cannot perform cross-modal fusion on a single image."
                )

        return True, None
