# backend/router/task_classifier.py
from typing import Dict, Any, Tuple
from backend.router.schemas import TaskType, InputType

class TaskClassifier:
    @staticmethod
    def classify_task(
        query_analysis: Dict[str, Any],
        input_type: InputType = InputType.UNKNOWN
    ) -> Tuple[TaskType, float]:
        """
        Classifies the required Remote Sensing TaskType and associated confidence.
        Prioritizes explicit queries such as Grounding, Optical-SAR, and Change Detection.
        """
        # 1. Optical + SAR Multimodal Analysis
        if query_analysis["has_optical_sar_cue"] or input_type == InputType.OPTICAL_SAR_PAIR:
            if query_analysis["has_optical_sar_cue"]:
                return TaskType.OPTICAL_SAR_ANALYSIS, 0.95
            return TaskType.OPTICAL_SAR_ANALYSIS, 0.85

        # 2. Visual Grounding / Localization
        if query_analysis["has_grounding_cue"]:
            return TaskType.GROUNDING, 0.92

        # 3. Change Detection & Change VQA
        if query_analysis["has_change_cue"]:
            if query_analysis["has_change_vqa_cue"]:
                return TaskType.CHANGE_VQA, 0.90
            return TaskType.CHANGE_DETECTION, 0.88

        # 4. Multi-temporal sequence
        if input_type == InputType.MULTI_TEMPORAL:
            return TaskType.MULTI_TEMPORAL_ANALYSIS, 0.85

        # 5. Object Analysis / Counting / Detection
        if query_analysis["has_object_cue"]:
            return TaskType.OBJECT_ANALYSIS, 0.85

        # 6. Scene Analysis & Land Cover
        if query_analysis["has_scene_cue"]:
            return TaskType.SCENE_ANALYSIS, 0.86

        # 7. Image Captioning
        if query_analysis["has_caption_cue"]:
            return TaskType.CAPTIONING, 0.89

        # 8. General Remote Sensing Visual Question Answering
        return TaskType.VQA, 0.80
