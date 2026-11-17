# backend/models/grounding_adapter.py
import time
import httpx
from typing import Dict, Any, List, Tuple, Optional
from backend.models.base_model import BaseModelAdapter
from backend.models.mock_adapter import MockSpecialistAdapter
from backend.config.settings import settings

class GroundingAdapter(BaseModelAdapter):
    """
    Adapter for Dedicated Visual Grounding Specialist.
    URL and endpoints configured via environment variables.
    """
    def __init__(self):
        super().__init__("grounding-specialist", "RS-GroundingSpecialist")
        self.mock_fallback = MockSpecialistAdapter("grounding-specialist", "RS-GroundingSpecialist", "Visual Grounding Specialist")

    def is_configured(self) -> bool:
        return bool(settings.GROUNDING_API_URL and settings.GROUNDING_API_URL.strip())

    async def health_check(self) -> Tuple[bool, str]:
        if not self.is_configured():
            if settings.ENABLE_MOCK_FALLBACK_FOR_TESTS:
                return True, "Grounding Specialist operating in MOCK mode (no live GROUNDING_API_URL set)."
            return False, "Grounding Specialist is not configured (GROUNDING_API_URL is empty)."

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(settings.GROUNDING_API_URL)
                if res.status_code < 500:
                    return True, f"Grounding endpoint reachable at {settings.GROUNDING_API_URL}."
                return False, f"Grounding endpoint returned status {res.status_code}."
        except Exception as e:
            return False, f"Failed to reach Grounding endpoint: {str(e)}"

    async def predict(
        self,
        query: str,
        file_paths: List[str],
        task: str,
        **kwargs
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        if not self.is_configured():
            if settings.ENABLE_MOCK_FALLBACK_FOR_TESTS:
                return await self.mock_fallback.predict(query, file_paths, task, **kwargs)
            raise RuntimeError("Grounding specialist is not configured. Set GROUNDING_API_URL in environment.")

        api_url = settings.GROUNDING_API_URL.rstrip("/")
        api_type = settings.GROUNDING_API_TYPE.lower()
        api_endpoint = settings.GROUNDING_API_ENDPOINT or "predict"

        try:
            async with httpx.AsyncClient(timeout=settings.MODEL_TIMEOUT) as client:
                if api_type == "gradio":
                    endpoint_url = f"{api_url}/api/{api_endpoint}"
                    payload = {"data": [file_paths[0], query]}
                else:
                    endpoint_url = f"{api_url}/{api_endpoint}"
                    payload = {"image_path": file_paths[0], "query": query, "task": task}

                res = await client.post(endpoint_url, json=payload)
                res.raise_for_status()
                data = res.json()

                answer = data.get("answer") or (data.get("data", [""])[0] if "data" in data else str(data))
                confidence = data.get("confidence")
                evidence = data.get("evidence", {
                    "text": data.get("explanation"),
                    "boxes": data.get("boxes", []),
                    "overlay_url": data.get("overlay_url")
                })

                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "answer": answer,
                    "confidence": confidence,
                    "evidence": evidence,
                    "is_simulated": False,
                    "model_latency_ms": latency_ms,
                    "raw_output": data
                }
        except Exception as e:
            if settings.ENABLE_MOCK_FALLBACK_FOR_TESTS:
                res = await self.mock_fallback.predict(query, file_paths, task, **kwargs)
                res["evidence"]["text"] = f"(Endpoint call failed: {str(e)}. Fallback to simulation active.)"
                return res
            raise RuntimeError(f"Grounding specialist execution failed: {str(e)}")
