# backend/router/router.py
"""
SatQuery AI — Query-Driven Routing Module
Independent backend routing engine implementing Section 4 & Section 8 requirements:
- Input mode (Single Image vs Double Image)
- Question interpretation and semantic intent
- Image relationship and sensor modality
- Input validation results
- Specialist model capabilities and availability
- Research configurations:
    * Configuration A — Fixed Routing
    * Configuration B — Query-Driven Routing
    * Configuration C — Query-Driven Routing with Selective Cross-Model Reasoning
"""

import time
import re
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple

from backend.router.schemas import (
    TaskType,
    InputType,
    ModalityType,
    ModelStatus,
    RoutingDecision,
    ModelCandidateScore,
    StructuredTaskSpecification,
    ImageMetadata,
    CompatibilityResult,
    ValidationResult
)
from backend.router.query_analyzer import QueryAnalyzer
from backend.router.model_registry import ModelRegistry

class RoutingConfiguration(str, Enum):
    CONFIG_A = "CONFIG_A"  # Fixed Routing (Mode + declared relationship)
    CONFIG_B = "CONFIG_B"  # Query-Driven Routing (Query semantics + metadata + validation)
    CONFIG_C = "CONFIG_C"  # Query-Driven Routing with Selective Cross-Model Reasoning

class TaskCategory(str, Enum):
    SCENE_UNDERSTANDING = "scene_understanding"
    IMAGE_DESCRIPTION = "image_description"
    OBJECT_LANDCOVER = "object_landcover"
    VISUAL_QUESTION_ANSWERING = "visual_question_answering"
    BITEMPORAL_CHANGE_DETECTION = "bitemporal_change_detection"
    OPTICAL_SAR_ANALYSIS = "optical_sar_analysis"
    UNSUPPORTED_OR_AMBIGUOUS = "unsupported_or_ambiguous"

class ModelInvocationTrace(Dict[str, Any]):
    """Record for each model invocation in selective cross-model reasoning."""
    pass

class SatQueryRouter:
    """
    Modular, query-driven router for remote-sensing specialist foundation models.
    """

    @classmethod
    def route_request(
        cls,
        input_mode: str,
        question: str,
        relationship: Optional[str],
        metadata_list: List[ImageMetadata],
        validation_result: Optional[ValidationResult],
        compatibility_result: Optional[CompatibilityResult],
        routing_config: str = "CONFIG_C"
    ) -> Dict[str, Any]:
        """
        Main routing entrypoint evaluating Configuration A, B, or C.
        """
        route_start = time.perf_counter()
        normalized_mode = (input_mode or "SINGLE_IMAGE").upper().strip()
        if normalized_mode in ("SINGLE", "SINGLE_IMAGE"):
            mode = "SINGLE_IMAGE"
        else:
            mode = "DOUBLE_IMAGE"

        normalized_rel = (relationship or "UNKNOWN").upper().strip()
        config = routing_config.upper().strip()
        if config not in (RoutingConfiguration.CONFIG_A, RoutingConfiguration.CONFIG_B, RoutingConfiguration.CONFIG_C):
            config = RoutingConfiguration.CONFIG_C

        # Step 1: Interpret Query Semantics & Generate Structured Task Specification
        semantic_info = cls._interpret_query(question)
        structured_task_spec = QueryAnalyzer.generate_task_specification(question, num_observations=len(metadata_list))

        # Step 2: Calculate Mathematical Candidate Scores (Paper Eq 3, 4, 8, 9)
        candidate_scores = cls._calculate_candidate_scores(
            mode=mode,
            relationship=normalized_rel,
            question=question,
            semantic_info=semantic_info,
            metadata_list=metadata_list,
            validation=validation_result
        )

        # Step 3: Determine Task Category based on Config
        if config == RoutingConfiguration.CONFIG_A:
            routing_decision = cls._route_fixed_config_a(
                mode=mode,
                relationship=normalized_rel,
                question=question,
                semantic_info=semantic_info,
                metadata_list=metadata_list,
                validation=validation_result
            )
        elif config == RoutingConfiguration.CONFIG_B:
            routing_decision = cls._route_query_driven_config_b(
                mode=mode,
                relationship=normalized_rel,
                question=question,
                semantic_info=semantic_info,
                metadata_list=metadata_list,
                validation=validation_result
            )
        else:  # CONFIG_C: Query-Driven with Selective Cross-Model Reasoning
            routing_decision = cls._route_cross_model_config_c(
                mode=mode,
                relationship=normalized_rel,
                question=question,
                semantic_info=semantic_info,
                metadata_list=metadata_list,
                validation=validation_result
            )

        routing_duration_ms = round((time.perf_counter() - route_start) * 1000, 2)
        routing_decision["routing_duration_ms"] = routing_duration_ms
        routing_decision["routing_config"] = config
        routing_decision["structured_task_spec"] = structured_task_spec
        routing_decision["candidate_scores"] = candidate_scores

        return routing_decision

    @classmethod
    def _interpret_query(cls, question: str) -> Dict[str, Any]:
        """
        Performs semantic query interpretation beyond bare keywords.
        Identifies question target, linguistic intent, and ambiguity.
        """
        q = (question or "").lower().strip()

        # Check for ambiguity
        is_ambiguous = False
        ambiguity_reason = None
        if len(q) < 4 or q in ("?", "analyze", "test", "look", "what", "what is this"):
            is_ambiguous = True
            ambiguity_reason = f"Query '{question}' is insufficiently specified to determine a targeted remote-sensing task."

        # Change intent patterns
        change_patterns = [
            r"\b(change|changes|changed|changing)\b",
            r"\b(difference|differences|differ|diff)\b",
            r"\b(new buildings?|new structures?|demolished|appeared|disappeared)\b",
            r"\b(increased|decreased|expanded|shrunk|growth)\b",
            r"\b(before and after|between these two|over time)\b"
        ]
        has_change_intent = any(re.search(pat, q) for pat in change_patterns)

        # Object & Landcover patterns
        object_patterns = [
            r"\b(identify|locate|count|where (is|are))\b",
            r"\b(roads?|buildings?|vegetation|trees?|water|rivers?|lakes?|airports?|aircraft|ships?)\b",
            r"\b(land[- ]?cover|land[- ]?use)\b"
        ]
        has_object_intent = any(re.search(pat, q) for pat in object_patterns)

        # Scene description patterns
        description_patterns = [
            r"\b(describe|description|summarize|summary|overview|scene)\b"
        ]
        has_description_intent = any(re.search(pat, q) for pat in description_patterns)

        # Optical-SAR patterns
        optical_sar_patterns = [
            r"\b(optical and sar|sar and optical|radar and optical|optical \+ sar)\b",
            r"\b(sentinel[- ]?1 and sentinel[- ]?2|s1 and s2|cross[- ]modal|joint representation)\b"
        ]
        has_optical_sar_intent = any(re.search(pat, q) for pat in optical_sar_patterns)

        # Single-image focus cue in double image mode (e.g. "in the first image", "in image 1")
        single_image_focus = bool(re.search(r"\b(first image|image 1|pre-image|before image|single image)\b", q))

        return {
            "raw_query": question,
            "has_change_intent": has_change_intent,
            "has_object_intent": has_object_intent,
            "has_description_intent": has_description_intent,
            "has_optical_sar_intent": has_optical_sar_intent,
            "single_image_focus": single_image_focus,
            "is_ambiguous": is_ambiguous,
            "ambiguity_reason": ambiguity_reason
        }

    @classmethod
    def _route_fixed_config_a(
        cls,
        mode: str,
        relationship: str,
        question: str,
        semantic_info: Dict[str, Any],
        metadata_list: List[ImageMetadata],
        validation: Optional[ValidationResult]
    ) -> Dict[str, Any]:
        """
        Configuration A — Fixed Routing:
        Routes rigidly using input mode and declared image relationship.
        No question-driven redirection or cross-model reasoning.
        """
        reasons = ["Configuration A active: Fixed routing based on declared input mode and relationship."]

        if mode == "SINGLE_IMAGE":
            task_cat = TaskCategory.SCENE_UNDERSTANDING
            selected_model = "geochat-7b"
            display_name = "GeoChat-7B"
            reasons.append("Single Image mode mapped directly to GeoChat-7B foundation specialist.")
            return cls._build_routing_record(
                selected_model_id=selected_model,
                selected_model_name=display_name,
                task_category=task_cat,
                task_type=TaskType.SCENE_ANALYSIS,
                reasons=reasons,
                is_executable=True,
                invoke_secondary_model=False
            )

        # Double Image Mode
        if relationship in ("BI_TEMPORAL", "BEFORE_AFTER"):
            task_cat = TaskCategory.BITEMPORAL_CHANGE_DETECTION
            selected_model = "changestar"
            display_name = "ChangeStar"
            reasons.append("Declared bi-temporal relationship mapped directly to ChangeStar change specialist.")
            return cls._build_routing_record(
                selected_model_id=selected_model,
                selected_model_name=display_name,
                task_category=task_cat,
                task_type=TaskType.CHANGE_DETECTION,
                reasons=reasons,
                is_executable=True,
                invoke_secondary_model=False
            )
        elif relationship in ("OPTICAL_SAR", "OPTICAL_AND_SAR"):
            task_cat = TaskCategory.OPTICAL_SAR_ANALYSIS
            selected_model = "croma"
            display_name = "CROMA"
            reasons.append("Declared Optical–SAR relationship mapped directly to CROMA multimodal foundation model.")
            return cls._build_routing_record(
                selected_model_id=selected_model,
                selected_model_name=display_name,
                task_category=task_cat,
                task_type=TaskType.OPTICAL_SAR_ANALYSIS,
                reasons=reasons,
                is_executable=True,
                invoke_secondary_model=False
            )
        else:
            # Unknown relationship in Fixed Routing
            reasons.append("Relationship is 'Unknown or other image pair'. Fixed Routing requires an explicit relationship specification.")
            return cls._build_routing_record(
                selected_model_id=None,
                selected_model_name=None,
                task_category=TaskCategory.UNSUPPORTED_OR_AMBIGUOUS,
                task_type=TaskType.UNKNOWN,
                reasons=reasons,
                is_executable=False,
                blocking_issue="Fixed Routing (Config A) cannot determine a specialist model when relationship is Unknown. Please specify the image pair relationship or switch to Query-Driven Routing (Config B/C)."
            )

    @classmethod
    def _route_query_driven_config_b(
        cls,
        mode: str,
        relationship: str,
        question: str,
        semantic_info: Dict[str, Any],
        metadata_list: List[ImageMetadata],
        validation: Optional[ValidationResult]
    ) -> Dict[str, Any]:
        """
        Configuration B — Query-Driven Routing:
        Routes intelligently based on user question, input mode, relationship, validation results, and model capabilities.
        No cross-model reasoning.
        """
        reasons = ["Configuration B active: Query-driven routing incorporating semantic intent and validation checks."]

        # 0. Check for Unsupported Domain Queries (Paper Section V-B Scenario 6)
        unsupported_keywords = ["weather", "temperature", "forecast", "climate model", "stock", "crypto", "soil chemistry"]
        if any(w in (question or "").lower() for w in unsupported_keywords):
            reasons.append(f"Domain Boundary (Stage 3): Requested query '{question}' is outside the capabilities of registered remote-sensing specialist workflows.")
            return cls._build_routing_record(
                selected_model_id=None,
                selected_model_name=None,
                task_category=TaskCategory.UNSUPPORTED_OR_AMBIGUOUS,
                task_type=TaskType.UNKNOWN,
                reasons=reasons,
                is_executable=False,
                blocking_issue=f"SatQuery AI focuses on remote-sensing visual understanding, change detection, and optical–SAR analysis. The query '{question}' falls outside registered specialist capabilities."
            )

        # 0a. Check for Physical / Spectral Incompatibility (Stage 3: e.g., NDVI on standard 3-channel RGB)
        if "ndvi" in (question or "").lower():
            has_nir = any(m.channels > 3 or m.detected_modality == ModalityType.MULTISPECTRAL for m in metadata_list)
            is_plain_rgb = all(m.channels == 3 for m in metadata_list) if metadata_list else True
            if is_plain_rgb and not has_nir:
                reasons.append("Compatibility Validation Failure (Stage 3): NDVI computation requires Near-Infrared (NIR) spectral bands (e.g., Sentinel-2 Band 8), which are absent in standard 3-channel RGB imagery.")
                return cls._build_routing_record(
                    selected_model_id=None,
                    selected_model_name=None,
                    task_category=TaskCategory.UNSUPPORTED_OR_AMBIGUOUS,
                    task_type=TaskType.UNKNOWN,
                    reasons=reasons,
                    is_executable=False,
                    blocking_issue="NDVI calculation requires Near-Infrared (NIR) bands not present in RGB imagery. Standard RGB channels (Red, Green, Blue) cannot compute normalized difference vegetation index."
                )

        # 0b. Check for Blocking Input Validation Errors (Paper Section III-B & Section V-B Scenario 4)
        if validation and not validation.is_valid and validation.blocking_errors:
            first_err = validation.blocking_errors[0]
            reasons.append(f"Input validation rejected observations (Stage 3): {first_err}")
            return cls._build_routing_record(
                selected_model_id=None,
                selected_model_name=None,
                task_category=TaskCategory.UNSUPPORTED_OR_AMBIGUOUS,
                task_type=TaskType.UNKNOWN,
                reasons=reasons,
                is_executable=False,
                blocking_issue=first_err
            )

        # 1. Check for ambiguous questions (Paper Section V-B Scenario 5)
        if semantic_info["is_ambiguous"]:
            reasons.append(f"Ambiguity noted: {semantic_info['ambiguity_reason']}")
            if mode == "DOUBLE_IMAGE":
                if relationship in ("OPTICAL_SAR", "OPTICAL_AND_SAR"):
                    reasons.append("Applying conservative default for double images: Defaulted to CROMA Optical-SAR representation learning.")
                    return cls._build_routing_record(
                        selected_model_id="croma",
                        selected_model_name="CROMA",
                        task_category=TaskCategory.OPTICAL_SAR_ANALYSIS,
                        task_type=TaskType.OPTICAL_SAR_ANALYSIS,
                        reasons=reasons,
                        is_executable=True,
                        invoke_secondary_model=False,
                        limitation="Defaulted to Optical-SAR analysis due to ambiguous query in dual-sensor mode."
                    )
                else:
                    reasons.append("Applying conservative default for double images: Defaulted to ChangeStar bi-temporal change detection.")
                    return cls._build_routing_record(
                        selected_model_id="changestar",
                        selected_model_name="ChangeStar",
                        task_category=TaskCategory.BITEMPORAL_CHANGE_DETECTION,
                        task_type=TaskType.CHANGE_DETECTION,
                        reasons=reasons,
                        is_executable=True,
                        invoke_secondary_model=False,
                        limitation="Defaulted to bi-temporal change detection due to ambiguous query in double-image mode."
                    )
            else:
                reasons.append("Applying conservative default: Routing to GeoChat-7B for general scene interpretation.")
                return cls._build_routing_record(
                    selected_model_id="geochat-7b",
                    selected_model_name="GeoChat-7B",
                    task_category=TaskCategory.SCENE_UNDERSTANDING,
                    task_type=TaskType.SCENE_ANALYSIS,
                    reasons=reasons,
                    is_executable=True,
                    invoke_secondary_model=False,
                    limitation="Assumed general scene understanding due to ambiguous query."
                )

        # 2. Single Image Mode handling
        if mode == "SINGLE_IMAGE":
            # Safety Gate: if query asks for change detection on 1 image, reject!
            if semantic_info["has_change_intent"]:
                reasons.append("Domain Rule Triggered: Change detection requires at least two temporal observations.")
                return cls._build_routing_record(
                    selected_model_id=None,
                    selected_model_name=None,
                    task_category=TaskCategory.UNSUPPORTED_OR_AMBIGUOUS,
                    task_type=TaskType.CHANGE_DETECTION,
                    reasons=reasons,
                    is_executable=False,
                    blocking_issue="Change analysis requires at least two temporal observations. Please switch to Double Image mode and upload before-and-after images."
                )

            # Object / Landcover query
            if semantic_info["has_object_intent"]:
                reasons.append("Identified object/land-cover query: Routing to GeoChat-7B for grounded visual interpretation.")
                return cls._build_routing_record(
                    selected_model_id="geochat-7b",
                    selected_model_name="GeoChat-7B",
                    task_category=TaskCategory.OBJECT_LANDCOVER,
                    task_type=TaskType.OBJECT_ANALYSIS,
                    reasons=reasons,
                    is_executable=True,
                    invoke_secondary_model=False
                )

            # Scene description query
            if semantic_info["has_description_intent"]:
                reasons.append("Identified scene description query: Routing to GeoChat-7B for remote-sensing image captioning.")
                return cls._build_routing_record(
                    selected_model_id="geochat-7b",
                    selected_model_name="GeoChat-7B",
                    task_category=TaskCategory.IMAGE_DESCRIPTION,
                    task_type=TaskType.CAPTIONING,
                    reasons=reasons,
                    is_executable=True,
                    invoke_secondary_model=False
                )

            # General VQA query
            reasons.append("Identified natural-language visual question: Routing to GeoChat-7B.")
            return cls._build_routing_record(
                selected_model_id="geochat-7b",
                selected_model_name="GeoChat-7B",
                task_category=TaskCategory.VISUAL_QUESTION_ANSWERING,
                task_type=TaskType.VQA,
                reasons=reasons,
                is_executable=True,
                invoke_secondary_model=False
            )

        # 3. Double Image Mode handling
        # Case 3a: Query specifically asks only about one image in a pair
        if semantic_info["single_image_focus"] and not semantic_info["has_change_intent"]:
            reasons.append("Query specifically queries a single observation within the pair: Routing to GeoChat-7B for primary image.")
            return cls._build_routing_record(
                selected_model_id="geochat-7b",
                selected_model_name="GeoChat-7B",
                task_category=TaskCategory.SCENE_UNDERSTANDING,
                task_type=TaskType.SCENE_ANALYSIS,
                reasons=reasons,
                is_executable=True,
                invoke_secondary_model=False
            )

        # Check if physical inputs represent genuine Optical + SAR
        has_sar_input = False
        has_optical_input = False
        if metadata_list and len(metadata_list) == 2:
            m_modalities = {m.detected_modality for m in metadata_list}
            m_channels = {m.channels for m in metadata_list}
            has_sar_input = ModalityType.SAR in m_modalities or 1 in m_channels or 2 in m_channels
            has_optical_input = ModalityType.OPTICAL in m_modalities or ModalityType.MULTISPECTRAL in m_modalities or any(c >= 3 for c in m_channels)
        is_optical_sar_input = has_sar_input and has_optical_input

        # Case 3b: Optical-SAR analysis
        if semantic_info["has_optical_sar_intent"] or relationship in ("OPTICAL_SAR", "OPTICAL_AND_SAR") or (is_optical_sar_input and not semantic_info["has_change_intent"]):
            # Hard compatibility constraint: check for authentic radar backscatter
            if validation and validation.modality_compatible is False:
                reasons.append("Compatibility Constraint Failed: Provided observations lack genuine radar backscatter channels.")
                return cls._build_routing_record(
                    selected_model_id=None,
                    selected_model_name=None,
                    task_category=TaskCategory.OPTICAL_SAR_ANALYSIS,
                    task_type=TaskType.OPTICAL_SAR_ANALYSIS,
                    reasons=reasons,
                    is_executable=False,
                    blocking_issue="Optical–SAR analysis requires authentic radar backscatter data (e.g. Sentinel-1 VV/VH). The provided optical RGB image does not contain radar data."
                )
            reasons.append("Routing to CROMA for Optical–SAR representation learning.")
            return cls._build_routing_record(
                selected_model_id="croma",
                selected_model_name="CROMA",
                task_category=TaskCategory.OPTICAL_SAR_ANALYSIS,
                task_type=TaskType.OPTICAL_SAR_ANALYSIS,
                reasons=reasons,
                is_executable=True,
                invoke_secondary_model=False
            )

        # Case 3c: Change Detection
        if semantic_info["has_change_intent"] or relationship in ("BI_TEMPORAL", "BEFORE_AFTER"):
            reasons.append("Detected bi-temporal change intent: Routing to ChangeStar change detection specialist.")
            return cls._build_routing_record(
                selected_model_id="changestar",
                selected_model_name="ChangeStar",
                task_category=TaskCategory.BITEMPORAL_CHANGE_DETECTION,
                task_type=TaskType.CHANGE_DETECTION,
                reasons=reasons,
                is_executable=True,
                invoke_secondary_model=False
            )

        # Case 3d: Double image pair with general comparative query
        reasons.append("Double image pair with structural comparison intent: Routing to ChangeStar.")
        return cls._build_routing_record(
            selected_model_id="changestar",
            selected_model_name="ChangeStar",
            task_category=TaskCategory.BITEMPORAL_CHANGE_DETECTION,
            task_type=TaskType.CHANGE_DETECTION,
            reasons=reasons,
            is_executable=True,
            invoke_secondary_model=False
        )

    @classmethod
    def _route_cross_model_config_c(
        cls,
        mode: str,
        relationship: str,
        question: str,
        semantic_info: Dict[str, Any],
        metadata_list: List[ImageMetadata],
        validation: Optional[ValidationResult]
    ) -> Dict[str, Any]:
        """
        Configuration C — Query-Driven Routing with Selective Cross-Model Reasoning:
        Uses query-driven routing for the primary model, and selectively determines whether
        a complementary specialist should be invoked.
        """
        # First obtain the primary query-driven decision from Config B
        primary_decision = cls._route_query_driven_config_b(
            mode=mode,
            relationship=relationship,
            question=question,
            semantic_info=semantic_info,
            metadata_list=metadata_list,
            validation=validation
        )

        if not primary_decision["is_executable"]:
            return primary_decision

        reasons = list(primary_decision["reasons"])
        reasons.append("Configuration C active: Evaluating justification for selective cross-model reasoning.")

        primary_model = primary_decision["selected_model_id"]
        invoke_secondary = False
        secondary_model = None
        secondary_role = None
        secondary_justification = None

        # Justification Check 1: ChangeStar + GeoChat
        # If ChangeStar produces a change map AND the user asks a natural-language explanatory question
        # (e.g. "What changes occurred?", "Where have new buildings appeared?"), invoke GeoChat to explain changed regions!
        if primary_model == "changestar":
            if semantic_info["has_change_intent"] and (semantic_info["has_description_intent"] or "what" in question.lower() or "where" in question.lower() or "why" in question.lower()):
                invoke_secondary = True
                secondary_model = "geochat-7b"
                secondary_role = "Semantic Change Describer"
                secondary_justification = (
                    "Cross-Model Reasoning Justified: ChangeStar outputs a quantitative spatial change mask; "
                    "GeoChat is selectively invoked to describe the semantic visual characteristics of the detected changes."
                )
                reasons.append(secondary_justification)

        # Justification Check 2: CROMA + Downstream similarity interpreter
        # CROMA is an encoder-only model. Embeddings require downstream evaluation.
        elif primary_model == "croma":
            # CROMA output is augmented with documented downstream cosine similarity analysis
            reasons.append("Cross-Model Reasoning Note: CROMA representations will be paired with deterministic downstream feature-correlation metrics.")

        # Justification Check 3: Single Image with GeoChat
        # No secondary model needed for single image scene questions
        elif primary_model == "geochat-7b":
            reasons.append("Single-image scene inquiry is fully supported by GeoChat; no secondary specialist model justified.")

        primary_decision["reasons"] = reasons
        primary_decision["invoke_secondary_model"] = invoke_secondary
        primary_decision["secondary_model_id"] = secondary_model
        primary_decision["secondary_model_role"] = secondary_role
        primary_decision["secondary_justification"] = secondary_justification

        return primary_decision

    @staticmethod
    def _build_routing_record(
        selected_model_id: Optional[str],
        selected_model_name: Optional[str],
        task_category: TaskCategory,
        task_type: TaskType,
        reasons: List[str],
        is_executable: bool,
        invoke_secondary_model: bool = False,
        secondary_model_id: Optional[str] = None,
        secondary_model_role: Optional[str] = None,
        blocking_issue: Optional[str] = None,
        limitation: Optional[str] = None
    ) -> Dict[str, Any]:
        return {
            "selected_model_id": selected_model_id,
            "selected_model_name": selected_model_name,
            "task_category": task_category.value,
            "detected_task": task_type,
            "reasons": reasons,
            "is_executable": is_executable,
            "blocking_issue": blocking_issue,
            "invoke_secondary_model": invoke_secondary_model,
            "secondary_model_id": secondary_model_id,
            "secondary_model_role": secondary_model_role,
            "limitation": limitation
        }

    @classmethod
    def _calculate_candidate_scores(
        cls,
        mode: str,
        relationship: str,
        question: str,
        semantic_info: Dict[str, Any],
        metadata_list: List[ImageMetadata],
        validation: Optional[ValidationResult]
    ) -> List[ModelCandidateScore]:
        """
        Paper Section IV-C to IV-E & Section V-D (Eq. 3, 4, 8, 9):
        Hard Constraint: C(W_k, X, T) in {0, 1}
        Feasible Set: W_f = {W_k | C(W_k, X, T) = 1}
        Scoring: S(w_i | q, x) = alpha*I(w_i, q) + beta*C_f(w_i, x) + gamma*M(w_i, x) - lambda*P(w_i, q, x)
        alpha=0.40, beta=0.30, gamma=0.20, lambda=0.50
        """
        alpha, beta, gamma, lam = 0.40, 0.30, 0.20, 0.50
        q_lower = (question or "").lower()
        candidates: List[ModelCandidateScore] = []

        # 1. GeoChat-7B
        st_gc, msg_gc = ModelRegistry.get_model_status("geochat-7b")
        c_gc = 1 if (mode == "SINGLE_IMAGE" or semantic_info.get("single_image_focus")) else 0
        if mode == "DOUBLE_IMAGE" and semantic_info.get("has_change_intent") and not semantic_info.get("single_image_focus"):
            c_gc = 0
        
        i_gc = 0.1 if (semantic_info.get("has_change_intent") and not semantic_info.get("single_image_focus")) else 0.95
        cf_gc = 1.0 if mode == "SINGLE_IMAGE" else 0.4
        m_gc = 1.0
        p_gc = 0.0
        if not c_gc:
            p_gc += 0.8
        if st_gc == ModelStatus.NOT_CONFIGURED:
            p_gc += 0.2
        s_gc = round(max(0.0, alpha * i_gc + beta * cf_gc + gamma * m_gc - lam * p_gc) if c_gc else 0.0, 4)
        
        candidates.append(
            ModelCandidateScore(
                model_id="geochat-7b",
                display_name="GeoChat-7B",
                total_score=s_gc,
                task_match_score=round(i_gc, 3),
                input_type_match_score=round(cf_gc, 3),
                modality_match_score=round(m_gc, 3),
                capability_match_score=0.90,
                compatibility_score=round(cf_gc, 3),
                availability_score=1.0 if st_gc == ModelStatus.AVAILABLE else (0.85 if st_gc == ModelStatus.MOCK else 0.0),
                availability_status=st_gc,
                status_message=msg_gc,
                intent_score=round(i_gc, 3),
                input_compatibility=round(cf_gc, 3),
                modality_score=round(m_gc, 3),
                penalty=round(p_gc, 3),
                is_feasible=bool(c_gc)
            )
        )

        # Check if physical inputs represent genuine Optical + SAR
        has_sar_input = False
        has_optical_input = False
        if metadata_list and len(metadata_list) == 2:
            m_modalities = {m.detected_modality for m in metadata_list}
            m_channels = {m.channels for m in metadata_list}
            has_sar_input = ModalityType.SAR in m_modalities or 1 in m_channels or 2 in m_channels
            has_optical_input = ModalityType.OPTICAL in m_modalities or ModalityType.MULTISPECTRAL in m_modalities or any(c >= 3 for c in m_channels)
        is_optical_sar_input = has_sar_input and has_optical_input

        # 2. ChangeStar
        st_cs, msg_cs = ModelRegistry.get_model_status("changestar")
        c_cs = 1 if (mode == "DOUBLE_IMAGE" and len(metadata_list) >= 2 and not is_optical_sar_input) else 0
        if mode == "DOUBLE_IMAGE" and len(metadata_list) >= 2 and relationship in ("BI_TEMPORAL", "BEFORE_AFTER"):
            c_cs = 1
        if mode == "SINGLE_IMAGE":
            c_cs = 0
        
        i_cs = 1.0 if (semantic_info.get("has_change_intent") or relationship in ("BI_TEMPORAL", "BEFORE_AFTER") or not is_optical_sar_input) else 0.25
        cf_cs = 1.0 if (validation is None or validation.spatial_aligned is not False) else 0.3
        m_cs = 1.0 if relationship in ("BI_TEMPORAL", "BEFORE_AFTER", "UNKNOWN") else 0.1
        p_cs = 0.0
        if not c_cs:
            p_cs += 0.8
        if validation and validation.spatial_aligned is False:
            p_cs += 0.4
        s_cs = round(max(0.0, alpha * i_cs + beta * cf_cs + gamma * m_cs - lam * p_cs) if c_cs else 0.0, 4)

        candidates.append(
            ModelCandidateScore(
                model_id="changestar",
                display_name="ChangeStar",
                total_score=s_cs,
                task_match_score=round(i_cs, 3),
                input_type_match_score=round(cf_cs, 3),
                modality_match_score=round(m_cs, 3),
                capability_match_score=1.0,
                compatibility_score=round(cf_cs, 3),
                availability_score=1.0 if st_cs == ModelStatus.AVAILABLE else (0.85 if st_cs == ModelStatus.MOCK else 0.0),
                availability_status=st_cs,
                status_message=msg_cs,
                intent_score=round(i_cs, 3),
                input_compatibility=round(cf_cs, 3),
                modality_score=round(m_cs, 3),
                penalty=round(p_cs, 3),
                is_feasible=bool(c_cs)
            )
        )

        # 3. CROMA
        st_cr, msg_cr = ModelRegistry.get_model_status("croma")
        c_cr = 1 if (mode == "DOUBLE_IMAGE" and len(metadata_list) >= 2) else 0
        if mode == "SINGLE_IMAGE":
            c_cr = 0
            
        i_cr = 1.0 if (semantic_info.get("has_optical_sar_intent") or relationship in ("OPTICAL_SAR", "OPTICAL_AND_SAR") or is_optical_sar_input) else 0.15
        cf_cr = 1.0 if (mode == "DOUBLE_IMAGE") else 0.0
        m_cr = 0.2 if (validation and validation.modality_compatible is False) else 1.0
        p_cr = 0.0
        if not c_cr:
            p_cr += 0.8
        if validation and validation.modality_compatible is False:
            p_cr += 0.5
        s_cr = round(max(0.0, alpha * i_cr + beta * cf_cr + gamma * m_cr - lam * p_cr) if c_cr else 0.0, 4)

        candidates.append(
            ModelCandidateScore(
                model_id="croma",
                display_name="CROMA",
                total_score=s_cr,
                task_match_score=round(i_cr, 3),
                input_type_match_score=round(cf_cr, 3),
                modality_match_score=round(m_cr, 3),
                capability_match_score=1.0,
                compatibility_score=round(cf_cr, 3),
                availability_score=1.0 if st_cr == ModelStatus.AVAILABLE else (0.85 if st_cr == ModelStatus.MOCK else 0.0),
                availability_status=st_cr,
                status_message=msg_cr,
                intent_score=round(i_cr, 3),
                input_compatibility=round(cf_cr, 3),
                modality_score=round(m_cr, 3),
                penalty=round(p_cr, 3),
                is_feasible=bool(c_cr)
            )
        )

        # 4. RS-GroundingSpecialist
        st_gr, msg_gr = ModelRegistry.get_model_status("grounding-specialist")
        c_gr = 1 if mode == "SINGLE_IMAGE" else 0
        i_gr = 0.95 if any(kw in q_lower for kw in ["highlight", "locate", "grounding", "bounding box", "where is", "where are"]) else 0.2
        cf_gr = 1.0 if mode == "SINGLE_IMAGE" else 0.0
        m_gr = 1.0
        p_gr = 0.5 if st_gr == ModelStatus.NOT_CONFIGURED else 0.0
        if not c_gr:
            p_gr += 0.8
        s_gr = round(max(0.0, alpha * i_gr + beta * cf_gr + gamma * m_gr - lam * p_gr) if c_gr else 0.0, 4)

        candidates.append(
            ModelCandidateScore(
                model_id="grounding-specialist",
                display_name="RS-GroundingSpecialist",
                total_score=s_gr,
                task_match_score=round(i_gr, 3),
                input_type_match_score=round(cf_gr, 3),
                modality_match_score=round(m_gr, 3),
                capability_match_score=1.0,
                compatibility_score=round(cf_gr, 3),
                availability_score=1.0 if st_gr == ModelStatus.AVAILABLE else (0.85 if st_gr == ModelStatus.MOCK else 0.0),
                availability_status=st_gr,
                status_message=msg_gr,
                intent_score=round(i_gr, 3),
                input_compatibility=round(cf_gr, 3),
                modality_score=round(m_gr, 3),
                penalty=round(p_gr, 3),
                is_feasible=bool(c_gr)
            )
        )

        candidates.sort(key=lambda c: (c.is_feasible, c.total_score), reverse=True)
        return candidates
