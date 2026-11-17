# backend/services/execution_service.py
import time
import uuid
from typing import List, Optional, Dict, Any
from backend.router.schemas import (
    AnalysisResponse,
    ExecutionStep,
    RoutingDecision,
    CompatibilityResult,
    ValidationResult,
    ImageMetadata,
    InputType,
    ModalityType
)
from backend.services.compatibility_engine import CompatibilityEngine
from backend.services.metadata_service import MetadataService
from backend.services.input_validator import InputValidator
from backend.router.router import SatQueryRouter, RoutingConfiguration
from backend.router.routing_engine import RoutingEngine
from backend.router.query_analyzer import QueryAnalyzer
from backend.models import get_adapter
from backend.services.cross_model_reasoner import SelectiveCrossModelReasoner
from backend.services.response_normalizer import ResponseNormalizer
from backend.services.downstream_analysis import DownstreamAnalysisLayer
from backend.services.language_generation_service import LanguageGenerationService
from backend.research.experiment_logger import ExperimentLogger
from backend.config.settings import settings
from pathlib import Path

class ExecutionService:
    @staticmethod
    async def execute_pipeline(
        file_paths: List[str],
        query: str,
        user_input_type: Optional[str] = None,
        user_modality: Optional[str] = None,
        date_1: Optional[str] = None,
        date_2: Optional[str] = None,
        routing_config: str = "CONFIG_C"
    ) -> AnalysisResponse:
        """
        Orchestrates the complete multi-step remote-sensing vision-language analysis pipeline:
        1. Input Ingestion
        2. Format Validation & Deep Structural Inspection
        3. Geospatial & Sensor Metadata Extraction
        4. Spatial & Temporal Compatibility Verification
        5. Query-Driven Routing (Config A, B, or C)
        6. Specialist Model Execution (GeoChat, ChangeStar, CROMA)
        7. Optional Selective Cross-Model Reasoning
        8. Evidence Grounding & Normalized Synthesis
        """
        pipeline_start = time.perf_counter()
        request_id = f"satquery_{uuid.uuid4().hex[:12]}"
        trace: List[ExecutionStep] = []
        step_idx = 1
        timings: Dict[str, float] = {}

        def record_step(component: str, msg: str, status: str = "completed", details: Optional[Dict] = None, start_t: float = 0.0):
            nonlocal step_idx
            dur = round((time.perf_counter() - start_t) * 1000, 2) if start_t > 0 else 1.0
            trace.append(
                ExecutionStep(
                    step=step_idx,
                    component=component,
                    status=status,
                    duration_ms=dur,
                    message=msg,
                    details=details
                )
            )
            step_idx += 1

        # Step 1: Input Ingestion
        t0 = time.perf_counter()
        record_step(
            "Input Ingestion",
            f"Received {len(file_paths)} raster asset(s) and query: '{query[:65]}...'",
            start_t=t0
        )

        # Step 2: Dedicated Validation Stage
        t_val = time.perf_counter()
        validation_result: ValidationResult = InputValidator.validate_saved_files(
            file_paths=file_paths,
            question=query,
            input_mode=user_input_type,
            relationship=user_modality
        )
        timings["validation_ms"] = round((time.perf_counter() - t_val) * 1000, 2)

        val_status = "completed" if validation_result.is_valid else "failed"
        record_step(
            "Input Validation Layer",
            f"Validated {len(validation_result.images)} image(s). Status: {'Passed' if validation_result.is_valid else 'Errors detected'}.",
            status=val_status,
            details={
                "spatial_aligned": validation_result.spatial_aligned,
                "warnings": validation_result.warnings,
                "blocking_errors": validation_result.blocking_errors
            },
            start_t=t_val
        )

        # Halt immediately if validation layer found blocking errors
        if not validation_result.is_valid and validation_result.blocking_errors:
            total_dur = (time.perf_counter() - pipeline_start) * 1000
            timings["total_duration_ms"] = round(total_dur, 2)
            first_err = validation_result.blocking_errors[0]
            record_step(
                "Execution Orchestrator",
                f"Execution halted by input validation: {first_err}",
                status="failed"
            )
            from backend.router.schemas import TaskType
            blocked_routing = RoutingDecision(
                selected_model_id=None,
                selected_model_name=None,
                detected_task=TaskType.UNKNOWN,
                detected_input_type=InputType.UNKNOWN,
                detected_modality=ModalityType.UNKNOWN,
                task_confidence=0.0,
                reasons=[f"Validation failed: {first_err}"],
                candidate_scores=[],
                execution_plan=[],
                is_executable=False,
                blocking_issue=first_err,
                structured_task_spec=QueryAnalyzer.generate_task_specification(query)
            )
            compat_dummy = CompatibilityResult(
                is_compatible=False,
                input_type=InputType.UNKNOWN,
                modality=ModalityType.UNKNOWN,
                validation_messages=validation_result.validation_messages,
                blocking_errors=validation_result.blocking_errors
            )
            response = ResponseNormalizer.build_response(
                request_id=request_id,
                query=query,
                routing=blocked_routing,
                compatibility=compat_dummy,
                metadata=[],
                execution_trace=trace,
                blocking_error=first_err,
                validation=validation_result,
                timings=timings,
                routing_config=routing_config,
                total_duration_ms=total_dur
            )
            ExperimentLogger.log_analysis(response, model_latency_ms=0.0)
            return response

        # Step 3: Metadata Extraction
        t0 = time.perf_counter()
        metadata_list = MetadataService.extract_all(file_paths, user_modality)
        record_step(
            "Metadata Extraction",
            f"Extracted dimensions, bands, and geospatial headers for {len(metadata_list)} image(s).",
            details={"images": [m.filename for m in metadata_list]},
            start_t=t0
        )

        # Step 4: Compatibility Engine
        t0 = time.perf_counter()
        compatibility_result = CompatibilityEngine.validate_inputs(
            file_paths=file_paths,
            user_input_type=user_input_type,
            user_modality=user_modality,
            date_1=date_1,
            date_2=date_2
        )
        record_step(
            "Compatibility Engine",
            f"Spatial & temporal consistency: {'Verified' if compatibility_result.is_compatible else 'Discrepancy noted'}.",
            details={"messages": compatibility_result.validation_messages},
            start_t=t0
        )

        # Step 5: Query-Driven Routing (Config A, B, or C)
        t_route = time.perf_counter()
        routing_info = SatQueryRouter.route_request(
            input_mode=user_input_type or ("SINGLE_IMAGE" if len(file_paths) == 1 else "DOUBLE_IMAGE"),
            question=query,
            relationship=user_modality or validation_result.relationship or ("BI_TEMPORAL" if len(file_paths) == 2 else "UNKNOWN"),
            metadata_list=metadata_list,
            validation_result=validation_result,
            compatibility_result=compatibility_result,
            routing_config=routing_config
        )
        timings["routing_ms"] = round((time.perf_counter() - t_route) * 1000, 2)

        # Convert to legacy RoutingDecision for schema alignment
        sec_model_name = None
        if routing_info.get("invoke_secondary_model") and routing_info.get("secondary_model_id"):
            try:
                sec_ad = get_adapter(routing_info["secondary_model_id"])
                sec_model_name = getattr(sec_ad, "display_name", routing_info["secondary_model_id"])
            except Exception:
                sec_model_name = "GeoChat-7B"

        plan = [f"Route to {routing_info.get('selected_model_name')} under {routing_config}"]
        if sec_model_name:
            plan.append(f"Selective secondary reasoning via {sec_model_name}")

        routing_decision = RoutingDecision(
            selected_model_id=routing_info.get("selected_model_id"),
            selected_model_name=routing_info.get("selected_model_name"),
            detected_task=routing_info.get("detected_task"),
            detected_input_type=compatibility_result.input_type,
            detected_modality=compatibility_result.modality,
            task_confidence=0.90,
            reasons=routing_info.get("reasons", []),
            candidate_scores=routing_info.get("candidate_scores", []),
            execution_plan=plan,
            is_executable=routing_info.get("is_executable", True),
            blocking_issue=routing_info.get("blocking_issue"),
            structured_task_spec=routing_info.get("structured_task_spec")
        )

        record_step(
            f"Routing Engine ({routing_config})",
            f"Task: {routing_decision.detected_task.value}. Model: {routing_decision.selected_model_name or 'None'}.",
            status="completed" if routing_decision.is_executable else "failed",
            details={
                "reasons": routing_decision.reasons,
                "invoke_secondary_model": routing_info.get("invoke_secondary_model", False)
            },
            start_t=t_route
        )

        # Handle early termination (incompatible or blocked)
        if not routing_decision.is_executable or routing_decision.selected_model_id is None:
            total_dur = (time.perf_counter() - pipeline_start) * 1000
            timings["total_duration_ms"] = round(total_dur, 2)
            record_step(
                "Execution Orchestrator",
                f"Execution halted: {routing_decision.blocking_issue}",
                status="failed"
            )
            response = ResponseNormalizer.build_response(
                request_id=request_id,
                query=query,
                routing=routing_decision,
                compatibility=compatibility_result,
                metadata=metadata_list,
                execution_trace=trace,
                blocking_error=routing_decision.blocking_issue,
                validation=validation_result,
                timings=timings,
                routing_config=routing_config,
                total_duration_ms=total_dur
            )
            ExperimentLogger.log_analysis(response, model_latency_ms=0.0)
            return response

        # Step 6: Execute Primary Specialist Adapter
        t_model = time.perf_counter()
        adapter = get_adapter(routing_decision.selected_model_id)
        try:
            model_output = await adapter.predict(
                query=query,
                file_paths=file_paths,
                task=routing_decision.detected_task.value
            )
            model_latency = model_output.get("model_latency_ms", 0.0)
            timings["model_inference_ms"] = model_latency
            record_step(
                f"Specialist Execution ({routing_decision.selected_model_name})",
                f"Primary specialist completed inference in {model_latency}ms.",
                start_t=t_model
            )
        except Exception as e:
            record_step(
                f"Specialist Execution ({routing_decision.selected_model_name})",
                f"Model execution error: {str(e)}",
                status="failed",
                start_t=t_model
            )
            total_dur = (time.perf_counter() - pipeline_start) * 1000
            timings["total_duration_ms"] = round(total_dur, 2)
            response = ResponseNormalizer.build_response(
                request_id=request_id,
                query=query,
                routing=routing_decision,
                compatibility=compatibility_result,
                metadata=metadata_list,
                execution_trace=trace,
                blocking_error=f"Model execution failed: {str(e)}",
                validation=validation_result,
                timings=timings,
                routing_config=routing_config,
                total_duration_ms=total_dur
            )
            ExperimentLogger.log_analysis(response, model_latency_ms=0.0)
            return response

        # Step 7: Optional Selective Cross-Model Reasoning (Configuration C)
        final_model_payload = model_output
        t_cross = time.perf_counter()
        if routing_info.get("invoke_secondary_model", False):
            cross_result = await SelectiveCrossModelReasoner.reason(
                query=query,
                file_paths=file_paths,
                primary_output=model_output,
                routing_info=routing_info
            )
            timings["cross_reasoning_ms"] = cross_result.get("cross_reasoning_duration_ms", 0.0)
            final_model_payload = {
                "answer": cross_result.get("answer"),
                "confidence": cross_result.get("confidence"),
                "evidence": cross_result.get("evidence"),
                "models_used": cross_result.get("models_used"),
                "model_latency_ms": timings.get("model_inference_ms", 0.0) + timings["cross_reasoning_ms"],
                "raw_output": model_output.get("raw_output")
            }
            record_step(
                "Selective Cross-Model Reasoning",
                f"Invoked secondary reasoning specialist. Synthesized joint visual-change evidence.",
                start_t=t_cross,
                details={"invocations": cross_result.get("invocations")}
            )
        else:
            timings["cross_reasoning_ms"] = 0.0

        # Step 7b: Downstream Analysis Layer
        t_downstream = time.perf_counter()
        mask_path = None
        if "evidence" in final_model_payload and "change_mask_url" in final_model_payload["evidence"]:
            m_url = final_model_payload["evidence"]["change_mask_url"]
            if m_url and str(m_url).startswith("/api/uploads/"):
                fname = str(m_url).replace("/api/uploads/", "")
                cand = Path(settings.UPLOAD_DIR) / fname
                if cand.exists():
                    mask_path = str(cand)

        downstream_findings = DownstreamAnalysisLayer.analyze(
            task=routing_decision.detected_task.value,
            model_name=routing_decision.selected_model_name or "Specialist",
            model_output=final_model_payload,
            query=query,
            mask_path=mask_path
        )
        timings["downstream_analysis_ms"] = round((time.perf_counter() - t_downstream) * 1000, 2)

        # Merge downstream findings into evidence
        if "evidence" not in final_model_payload or not isinstance(final_model_payload["evidence"], dict):
            final_model_payload["evidence"] = {}
        final_model_payload["evidence"]["downstream_findings"] = downstream_findings
        if "spatial_distribution" in downstream_findings:
            final_model_payload["evidence"]["spatial_distribution"] = downstream_findings["spatial_distribution"]

        record_step(
            "Downstream Analysis Layer",
            downstream_findings.get("findings_summary", "Completed analytical decomposition."),
            start_t=t_downstream,
            details={
                "task": downstream_findings.get("task"),
                "semantic_classification_available": downstream_findings.get("semantic_classification_available", False),
                "metrics": downstream_findings.get("metrics", {})
            }
        )

        # Step 7c: Grounded Natural-Language Answer Generation
        t_lang = time.perf_counter()
        secondary_out = cross_result if routing_info.get("invoke_secondary_model", False) else None
        grounded_answer = await LanguageGenerationService.generate_grounded_answer(
            query=query,
            task=routing_decision.detected_task.value,
            model_name=routing_decision.selected_model_name or "Specialist",
            model_output=final_model_payload,
            downstream_findings=downstream_findings,
            validation_warnings=validation_result.warnings if validation_result else [],
            secondary_output=secondary_out
        )
        timings["language_generation_ms"] = round((time.perf_counter() - t_lang) * 1000, 2)
        final_model_payload["answer"] = grounded_answer

        record_step(
            "Language Generation Layer",
            "Synthesized evidence-grounded natural-language response directly addressing user inquiry.",
            start_t=t_lang,
            details={"answer_length": len(grounded_answer)}
        )

        # Step 8: Evidence Normalization & Final Response Assembly
        t0 = time.perf_counter()
        total_dur = (time.perf_counter() - pipeline_start) * 1000
        timings["total_duration_ms"] = round(total_dur, 2)
        record_step(
            "Evidence Fusion & Telemetry Assembly",
            "Synthesized grounded response, visual evidence links, and execution telemetry.",
            start_t=t0
        )

        response = ResponseNormalizer.build_response(
            request_id=request_id,
            query=query,
            routing=routing_decision,
            compatibility=compatibility_result,
            metadata=metadata_list,
            execution_trace=trace,
            model_result=final_model_payload,
            validation=validation_result,
            timings=timings,
            routing_config=routing_config,
            total_duration_ms=total_dur
        )

        # Step 9: Log Experiment Record
        ExperimentLogger.log_analysis(response, model_latency_ms=final_model_payload.get("model_latency_ms", 0.0))

        return response
