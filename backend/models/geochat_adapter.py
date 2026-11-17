# backend/models/geochat_adapter.py
"""
Adapter for GeoChat-7B: Grounded Large Vision-Language Model for Remote Sensing.
Section 3 & Section 4: Authoritative configuration via model_endpoints.yaml.

Rules:
- Reads endpoint and connection settings exclusively via CentralConfigManager (model_endpoints.yaml).
- No hardcoded endpoints in source code.
- Supports both Gradio API interface and REST API conventions.
- Only reports success when genuine inference response is returned.
- Never fabricates outputs; raises RuntimeError when unconfigured or offline in production.
"""

import os
import time
import httpx
import logging
from typing import Dict, Any, List, Tuple, Optional
from backend.models.base_model import BaseModelAdapter
from backend.models.mock_adapter import MockSpecialistAdapter
from backend.config.endpoint_config import CentralConfigManager, ServiceConfig
from backend.config.settings import settings
from backend.preprocessing.geochat_preprocessor import GeoChatPreprocessor

logger = logging.getLogger("GeoChatAdapter")

class GeoChatAdapter(BaseModelAdapter):
    def __init__(self):
        super().__init__("geochat-7b", "GeoChat-7B")
        self.preprocessor = GeoChatPreprocessor()
        self.mock_fallback = MockSpecialistAdapter("geochat-7b", "GeoChat-7B", "VLM Specialist")

    def get_service_config(self) -> ServiceConfig:
        """Retrieves authoritative configuration from model_endpoints.yaml."""
        return CentralConfigManager.get_config().get_service("geochat")

    def is_configured(self) -> bool:
        """
        Returns True if geochat service has a valid, non-placeholder URL
        in model_endpoints.yaml.
        """
        cfg = self.get_service_config()
        if cfg.is_configured():
            return True
        # Backwards compatibility check with settings/env if explicitly overridden
        legacy_url = getattr(settings, "GEOCHAT_API_URL", None)
        if legacy_url and str(legacy_url).strip() and "REPLACE-WITH" not in str(legacy_url):
            return True
        return False

    async def health_check(self) -> Tuple[bool, str]:
        if not self.is_configured():
            if settings.ENABLE_MOCK_FALLBACK_FOR_TESTS:
                return True, "GeoChat-7B operating in MOCK mode (explicit test fallback active)."
            return False, "GeoChat-7B is not configured. Set 'services.geochat.base_url' in backend/config/model_endpoints.yaml."

        cfg = self.get_service_config()
        url = cfg.base_url if cfg.is_configured() else settings.GEOCHAT_API_URL

        headers = {}
        api_key = cfg.get_api_key() or os.getenv("GEOCHAT_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                res = await client.get(url)
                if res.status_code < 500:
                    return True, f"GeoChat endpoint reachable at {url} (HTTP {res.status_code})."
                return False, f"GeoChat endpoint returned status {res.status_code}."
        except Exception as e:
            return False, f"Failed to reach GeoChat endpoint at {url}: {str(e)}"

    async def predict(
        self,
        query: str,
        file_paths: List[str],
        task: str,
        **kwargs
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        # Check configuration
        if not self.is_configured():
            if settings.ENABLE_MOCK_FALLBACK_FOR_TESTS:
                return await self.mock_fallback.predict(query, file_paths, task, **kwargs)
            raise RuntimeError(
                "GeoChat-7B specialist model is unavailable. "
                "Configure 'services.geochat.base_url' in backend/config/model_endpoints.yaml."
            )

        if not file_paths or not os.path.exists(file_paths[0]):
            raise FileNotFoundError(f"Input image file for GeoChat-7B not found: {file_paths}")

        cfg = self.get_service_config()
        base_url = (cfg.base_url if cfg.is_configured() else settings.GEOCHAT_API_URL or "").rstrip("/")
        api_type = cfg.api_type.lower() if cfg.is_configured() else getattr(settings, "GEOCHAT_API_TYPE", "gradio").lower()
        timeout = cfg.timeout_seconds if cfg.is_configured() else settings.MODEL_TIMEOUT

        headers = {}
        api_key = cfg.get_api_key() or os.getenv("GEOCHAT_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # 1. Gradio API invocation
        if api_type == "gradio":
            api_name = cfg.api_name or getattr(settings, "GEOCHAT_API_ENDPOINT", "predict") or "predict"
            endpoint_url = f"{base_url}/api/{api_name.lstrip('/')}"

            try:
                # Try gradio_client if available
                from gradio_client import Client, handle_file
                gradio_cl = Client(base_url, verbose=False, headers=headers if headers else None)
                pred_res = gradio_cl.predict(
                    handle_file(file_paths[0]),
                    query,
                    api_name=f"/{api_name.lstrip('/')}"
                )
                answer_text = str(pred_res)
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "answer": answer_text,
                    "confidence": None,
                    "evidence": {
                        "text": f"GeoChat-7B vision-language interpretation completed via Gradio ({base_url}).",
                        "regions": [],
                        "boxes": []
                    },
                    "is_simulated": False,
                    "model_latency_ms": latency_ms,
                    "raw_output": {"data": pred_res}
                }
            except Exception as gr_err:
                logger.info(f"gradio_client attempt returned: {gr_err}. Attempting direct HTTP POST fallback.")
                # Fallback to direct HTTP POST to Gradio /api/predict or /run/predict
                try:
                    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
                        payload = {"data": [file_paths[0], query]}
                        res = await client.post(endpoint_url, json=payload)
                        if res.status_code == 404:
                            # Try /run/predict format
                            res = await client.post(f"{base_url}/run/{api_name.lstrip('/')}", json=payload)

                        res.raise_for_status()
                        data = res.json()
                        answer = data.get("answer") or (data.get("data", [""])[0] if "data" in data else str(data))
                        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                        return {
                            "answer": answer,
                            "confidence": data.get("confidence"),
                            "evidence": data.get("evidence", {
                                "text": f"GeoChat-7B remote inference completed via {base_url}.",
                                "regions": [],
                                "boxes": data.get("boxes", [])
                            }),
                            "is_simulated": False,
                            "model_latency_ms": latency_ms,
                            "raw_output": data
                        }
                except Exception as http_err:
                    if settings.ENABLE_MOCK_FALLBACK_FOR_TESTS:
                        res = await self.mock_fallback.predict(query, file_paths, task, **kwargs)
                        res["evidence"]["text"] = f"(Endpoint call failed: {str(http_err)}. Fallback to simulation active.)"
                        return res
                    raise RuntimeError(f"GeoChat-7B Gradio inference failed at {base_url}: {str(http_err)}")

        # 2. Standard REST API invocation
        else:
            analyze_path = (cfg.analyze_path or "/predict").lstrip("/")
            endpoint_url = f"{base_url}/{analyze_path}"

            try:
                async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
                    payload = {"image_path": file_paths[0], "query": query, "task": task}
                    res = await client.post(endpoint_url, json=payload)
                    res.raise_for_status()
                    data = res.json()

                    answer = data.get("answer") or str(data)
                    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                    return {
                        "answer": answer,
                        "confidence": data.get("confidence"),
                        "evidence": data.get("evidence", {
                            "text": f"GeoChat-7B REST inference completed via {base_url}.",
                            "regions": [],
                            "boxes": data.get("boxes", [])
                        }),
                        "is_simulated": False,
                        "model_latency_ms": latency_ms,
                        "raw_output": data
                    }
            except Exception as e:
                if settings.ENABLE_MOCK_FALLBACK_FOR_TESTS:
                    res = await self.mock_fallback.predict(query, file_paths, task, **kwargs)
                    res["evidence"]["text"] = f"(Endpoint call failed: {str(e)}. Fallback to simulation active.)"
                    return res
                raise RuntimeError(f"GeoChat-7B REST inference failed at {base_url}: {str(e)}")
