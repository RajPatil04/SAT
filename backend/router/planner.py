# backend/router/planner.py
from typing import List, Dict, Any
from backend.router.schemas import TaskType, InputType, ModalityType

class ExecutionPlanner:
    @staticmethod
    def create_plan(
        task: TaskType,
        input_type: InputType,
        modality: ModalityType,
        selected_model: str
    ) -> List[str]:
        """
        Synthesizes a deterministic, explainable multi-step execution plan
        for the agentic orchestration engine.
        """
        plan = []

        if task in (TaskType.CHANGE_DETECTION, TaskType.CHANGE_VQA):
            plan.extend([
                "validate_bitemporal_image_pair",
                "verify_spatial_co_registration",
                "align_temporal_epoch_metadata",
                f"preprocess_for_change_specialist({selected_model})",
                f"execute_{selected_model}_dense_inference",
                "extract_change_vector_mask",
                "quantify_pixel_changes_and_regions",
                "generate_evidence_grounded_change_narrative"
            ])
        elif task == TaskType.OPTICAL_SAR_ANALYSIS:
            plan.extend([
                "validate_optical_and_sar_inputs",
                "verify_cross_modal_spatial_alignment",
                "extract_optical_spectral_features",
                "extract_sar_backscatter_intensity",
                f"execute_{selected_model}_cross_attention_fusion",
                "synthesize_joint_multimodal_evidence",
                "generate_multimodal_grounded_response"
            ])
        elif task == TaskType.GROUNDING:
            plan.extend([
                "validate_single_raster_input",
                "parse_spatial_referring_expression",
                f"execute_{selected_model}_spatial_grounding",
                "extract_bounding_boxes_and_coordinates",
                "generate_visual_grounding_overlay",
                "return_grounded_referential_response"
            ])
        elif task == TaskType.CAPTIONING:
            plan.extend([
                "validate_raster_input",
                "extract_image_structural_metadata",
                f"execute_{selected_model}_dense_captioning",
                "verify_land_cover_lexicon",
                "return_scene_description"
            ])
        else: # General VQA / Scene / Object
            plan.extend([
                "validate_input_image",
                "extract_metadata_and_bands",
                f"execute_{selected_model}_vqa_inference",
                "verify_response_grounding",
                "return_evidence_grounded_answer"
            ])

        return plan
