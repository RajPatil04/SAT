# backend/router/routing_engine.py
import time
from typing import List, Optional, Dict, Any
from backend.router.schemas import (
    TaskType,
    InputType,
    ModalityType,
    ModelStatus,
    RoutingDecision,
    CompatibilityResult,
    ImageMetadata
)
from backend.router.query_analyzer import QueryAnalyzer
from backend.router.task_classifier import TaskClassifier
from backend.router.input_classifier import InputClassifier
from backend.router.capability_matcher import CapabilityMatcher
from backend.router.routing_rules import RoutingRules
from backend.router.planner import ExecutionPlanner

class RoutingEngine:
    @staticmethod
    def route(
        query: str,
        images_metadata: List[ImageMetadata],
        compatibility: CompatibilityResult,
        user_input_type: Optional[str] = None
    ) -> RoutingDecision:
        """
        Executes the intelligent routing algorithm.
        Considers query intent, asset modalities, spatial/temporal compatibility,
        and scores candidate models against the mathematical formulation.
        """
        reasons = []

        # 1. Query Analysis
        query_analysis = QueryAnalyzer.analyze_query(query)
        reasons.append(f"Analyzed query semantics: identified {len(query_analysis['tokens'])} tokens.")
        if query_analysis["target_entities"]:
            reasons.append(f"Detected target entities: {', '.join(query_analysis['target_entities'])}.")

        # 2. Input Type & Modality Determination
        detected_input_type = InputClassifier.classify_input(
            images_metadata=images_metadata,
            user_input_type=user_input_type,
            query_cue_optical_sar=query_analysis["has_optical_sar_cue"]
        )
        detected_modality = compatibility.modality
        reasons.append(f"Input classification: {detected_input_type.value} with modality {detected_modality.value}.")

        # 3. Task Classification
        detected_task, task_confidence = TaskClassifier.classify_task(
            query_analysis=query_analysis,
            input_type=detected_input_type
        )
        reasons.append(f"Classified remote sensing task: {detected_task.value} (confidence: {task_confidence:.2f}).")

        # 4. Consistency & Pre-routing Domain Validation
        is_consistent, consistency_error = RoutingRules.validate_task_input_consistency(
            task=detected_task,
            input_type=detected_input_type,
            num_images=len(images_metadata),
            modality=detected_modality,
            query=query
        )

        if not is_consistent:
            reasons.append(f"Routing halted by domain rule: {consistency_error}")
            return RoutingDecision(
                selected_model_id=None,
                selected_model_name=None,
                detected_task=detected_task,
                detected_input_type=detected_input_type,
                detected_modality=detected_modality,
                task_confidence=task_confidence,
                reasons=reasons,
                candidate_scores=[],
                execution_plan=[],
                is_executable=False,
                blocking_issue=consistency_error
            )

        # 5. Score and Rank Candidate Models
        candidates = CapabilityMatcher.rank_candidates(
            task=detected_task,
            input_type=detected_input_type,
            modality=detected_modality,
            compatibility=compatibility
        )

        # 6. Model Selection
        selected_candidate = None
        for cand in candidates:
            # Check if model has non-zero task/input match and is available or in mock mode
            if cand.task_match_score > 0 and cand.input_type_match_score > 0:
                if cand.availability_status in (ModelStatus.AVAILABLE, ModelStatus.MOCK):
                    selected_candidate = cand
                    break

        if not selected_candidate:
            # Check if best candidate exists but is unconfigured
            top_cand = candidates[0] if candidates else None
            top_name = top_cand.display_name if top_cand else "specialist"
            status_desc = top_cand.availability_status.value if top_cand else "UNAVAILABLE"
            err_msg = (
                f"No compatible model for task '{detected_task.value}' is currently online or configured. "
                f"Target specialist '{top_name}' status is {status_desc}."
            )
            reasons.append(err_msg)
            return RoutingDecision(
                selected_model_id=top_cand.model_id if top_cand else None,
                selected_model_name=top_cand.display_name if top_cand else None,
                detected_task=detected_task,
                detected_input_type=detected_input_type,
                detected_modality=detected_modality,
                task_confidence=task_confidence,
                reasons=reasons,
                candidate_scores=candidates,
                execution_plan=[],
                is_executable=False,
                blocking_issue=err_msg
            )

        selected_model_id = selected_candidate.model_id
        selected_model_name = selected_candidate.display_name

        reasons.append(
            f"Selected specialist '{selected_model_name}' (ID: {selected_model_id}) "
            f"with score {selected_candidate.total_score:.3f} (Availability: {selected_candidate.availability_status.value})."
        )

        # 7. Generate Sequential Execution Plan
        plan = ExecutionPlanner.create_plan(
            task=detected_task,
            input_type=detected_input_type,
            modality=detected_modality,
            selected_model=selected_model_id
        )

        return RoutingDecision(
            selected_model_id=selected_model_id,
            selected_model_name=selected_model_name,
            detected_task=detected_task,
            detected_input_type=detected_input_type,
            detected_modality=detected_modality,
            task_confidence=task_confidence,
            reasons=reasons,
            candidate_scores=candidates,
            execution_plan=plan,
            is_executable=True,
            blocking_issue=None
        )
