# backend/services/cross_model_reasoner.py
import time
from typing import Dict, Any, List, Optional
from backend.models import get_adapter

class SelectiveCrossModelReasoner:
    """
    Executes selective cross-model reasoning according to Section 6.
    Invokes complementary specialists only when relevant, compatible, available, and justified.
    Records why each model was selected, inputs supplied, outputs, and whether used in final answer.
    """

    @classmethod
    async def reason(
        cls,
        query: str,
        file_paths: List[str],
        primary_output: Dict[str, Any],
        routing_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Orchestrates cross-model reasoning synthesis.
        """
        start_t = time.perf_counter()
        invocations: List[Dict[str, Any]] = []

        primary_model_name = routing_info.get("selected_model_name") or "Primary Specialist"
        primary_evidence = primary_output.get("evidence", {})

        # Record Primary Model Invocation
        invocations.append({
            "model_name": primary_model_name,
            "role": "Primary Specialist",
            "selection_reason": routing_info.get("reasons", ["Primary task selection"])[0],
            "input_supplied": [os_basename(p) for p in file_paths],
            "output_summary": str(primary_output.get("answer", ""))[:120] + "...",
            "used_in_final_answer": True,
            "latency_ms": primary_output.get("model_latency_ms", 0.0),
            "errors": None
        })

        invoke_secondary = routing_info.get("invoke_secondary_model", False)
        secondary_model_id = routing_info.get("secondary_model_id")

        if not invoke_secondary or not secondary_model_id:
            # Single-model reasoning
            return {
                "answer": primary_output.get("answer", ""),
                "models_used": [primary_model_name],
                "evidence": primary_evidence,
                "confidence": primary_output.get("confidence"),
                "invocations": invocations,
                "cross_reasoning_duration_ms": 0.0,
                "disclosed_agreements": None
            }

        # Execute Secondary Specialist (e.g. ChangeStar + GeoChat)
        secondary_start = time.perf_counter()
        secondary_adapter = get_adapter(secondary_model_id)
        secondary_name = getattr(secondary_adapter, "display_name", secondary_model_id)

        # Check if secondary adapter is configured
        is_sec_configured = getattr(secondary_adapter, "is_configured", lambda: False)()
        if not is_sec_configured:
            # Secondary model is not configured.
            # Do not invoke predict, do not invent answers, and do not report as executed.
            invocations.append({
                "model_name": secondary_name,
                "role": routing_info.get("secondary_model_role", "Secondary Reasoner"),
                "selection_reason": routing_info.get("secondary_justification", "Synthesize semantic description"),
                "input_supplied": [os_basename(p) for p in file_paths],
                "output_summary": None,
                "used_in_final_answer": False,
                "latency_ms": 0.0,
                "errors": f"{secondary_name} is unconfigured. Secondary semantic interpretation was skipped without fabrication."
            })
            return {
                "answer": primary_output.get("answer", ""),
                "models_used": [primary_model_name],
                "evidence": primary_evidence,
                "confidence": primary_output.get("confidence"),
                "invocations": invocations,
                "cross_reasoning_duration_ms": 0.0,
                "disclosed_agreements": None
            }

        change_pct = primary_evidence.get("change_percentage", 0.0)
        changed_px = primary_evidence.get("changed_pixels", 0)
        total_px = primary_evidence.get("total_pixels", 0)

        secondary_prompt = (
            f"A bi-temporal change detection specialist evaluated {change_pct}% changed surface area "
            f"({changed_px} changed pixels out of {total_px} total pixels) between these two temporal satellite images. "
            f"Provide a natural-language visual description of what specific features, land-cover shifts, or structures "
            f"appear to account for this change, addressing the user's question: '{query}'."
        )

        try:
            sec_output = await secondary_adapter.predict(
                query=secondary_prompt,
                file_paths=file_paths,
                task="CHANGE_VQA"
            )

            # Prevent any mock/simulated output from leaking into genuine inference
            if sec_output.get("is_simulated", False):
                raise RuntimeError(f"{secondary_name} returned simulated mock output; genuine inference required.")

            sec_latency = round((time.perf_counter() - secondary_start) * 1000, 2)
            sec_answer = sec_output.get("answer", "")

            # Record Secondary Model Invocation
            invocations.append({
                "model_name": secondary_name,
                "role": routing_info.get("secondary_model_role", "Secondary Reasoner"),
                "selection_reason": routing_info.get("secondary_justification", "Synthesize semantic description"),
                "input_supplied": [os_basename(p) for p in file_paths],
                "output_summary": str(sec_answer)[:120] + "...",
                "used_in_final_answer": True,
                "latency_ms": sec_latency,
                "errors": None
            })

            # Grounded joint answer synthesis
            synthesized_answer = (
                f"{primary_output.get('answer', '')}\n\n"
                f"Visual Change Interpretation ({secondary_name}):\n{sec_answer}\n\n"
                f"Evidence Grounding: ChangeStar generated the empirical change probability mask ({change_pct}% coverage). "
                f"{secondary_name} supplied visual semantic interpretation. Note that detected image differences represent model inferences and should be field-verified."
            )

            # Merge evidence
            merged_evidence = dict(primary_evidence)
            merged_evidence["secondary_explanation"] = sec_answer
            merged_evidence["cross_model_reasoning"] = True

            total_cross_ms = round((time.perf_counter() - start_t) * 1000, 2)

            return {
                "answer": synthesized_answer,
                "models_used": [primary_model_name, secondary_name],
                "evidence": merged_evidence,
                "confidence": primary_output.get("confidence"),  # Retain empirical change detector confidence
                "invocations": invocations,
                "cross_reasoning_duration_ms": total_cross_ms,
                "disclosed_agreements": (
                    f"Quantitative change detector ({primary_model_name}) and semantic visual reasoner ({secondary_name}) "
                    f"both analyzed the temporal pair. ChangeStar delineated spatial boundaries, and {secondary_name} characterized visual features."
                )
            }

        except Exception as e:
            # Secondary model failed: return primary change detection result alone without fabricated interpretation
            invocations.append({
                "model_name": secondary_name,
                "role": "Secondary Reasoner",
                "selection_reason": routing_info.get("secondary_justification", "Synthesize semantic description"),
                "input_supplied": [os_basename(p) for p in file_paths],
                "output_summary": None,
                "used_in_final_answer": False,
                "latency_ms": 0.0,
                "errors": f"Secondary model failed: {str(e)}"
            })

            return {
                "answer": primary_output.get("answer", ""),
                "models_used": [primary_model_name],
                "evidence": primary_evidence,
                "confidence": primary_output.get("confidence"),
                "invocations": invocations,
                "cross_reasoning_duration_ms": round((time.perf_counter() - start_t) * 1000, 2),
                "disclosed_agreements": None
            }

def os_basename(p: str) -> str:
    import os
    return os.path.basename(p)
