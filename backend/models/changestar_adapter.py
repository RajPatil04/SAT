# backend/models/changestar_adapter.py
import time
import os
import base64
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import httpx

from backend.models.base_model import BaseModelAdapter
from backend.models.mock_adapter import MockSpecialistAdapter
from backend.config.endpoint_config import CentralConfigManager, ServiceConfig
from backend.config.settings import settings
from backend.preprocessing.change_preprocessor import ChangePreprocessor

class ChangeStarAdapter(BaseModelAdapter):
    """
    Dedicated Adapter for ChangeStar (ResNet-18, LEVIR-CD fine-tuned).
    Exposes a consistent inference interface for bi-temporal remote-sensing change detection.
    Supports:
    1. Dedicated HTTP microservice configured in model_endpoints.yaml (default port 8001)
    2. In-process execution via ChangeStarEngine when microservice is offline
    3. Research mock fallback strictly when ENABLE_MOCK_FALLBACK_FOR_TESTS is active
    """
    def __init__(self):
        super().__init__("changestar", "ChangeStar")
        self.preprocessor = ChangePreprocessor()
        self.mock_fallback = MockSpecialistAdapter("changestar", "ChangeStar", "Bi-temporal Change Specialist")

    def get_service_config(self) -> ServiceConfig:
        return CentralConfigManager.get_config().get_service("changestar")

    def is_configured(self) -> bool:
        cfg = self.get_service_config()
        if cfg.is_configured():
            return True
        if settings.CHANGE_MODEL_API_URL and settings.CHANGE_MODEL_API_URL.strip():
            return True
        # Check if local weights exist
        weights_path = Path(__file__).resolve().parent.parent.parent / "pretrained_weights" / "changestar1x96_r18_ft_levircd.pth"
        return weights_path.exists()

    async def health_check(self) -> Tuple[bool, str]:
        cfg = self.get_service_config()
        base_url = cfg.base_url if cfg.is_configured() else settings.CHANGE_MODEL_API_URL

        # 1. Try microservice if URL is configured
        if base_url and base_url.strip():
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    res = await client.get(f"{base_url.rstrip('/')}/health")
                    if res.status_code == 200:
                        data = res.json()
                        return True, f"ChangeStar microservice ONLINE at {base_url} ({data.get('device', 'cpu')})."
            except Exception:
                pass

        # 2. Check local weights
        weights_path = Path(__file__).resolve().parent.parent.parent / "pretrained_weights" / "changestar1x96_r18_ft_levircd.pth"
        if weights_path.exists():
            return True, f"ChangeStar weights available locally ({weights_path.stat().st_size / (1024*1024):.1f} MB). Ready for in-process inference."

        if settings.ENABLE_MOCK_FALLBACK_FOR_TESTS:
            return True, "ChangeStar operating in MOCK mode (no weights or microservice configured)."

        return False, "ChangeStar is unconfigured: microservice offline and pretrained weights not found."

    async def predict(
        self,
        query: str,
        file_paths: List[str],
        task: str,
        **kwargs
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        # Input validation
        if len(file_paths) < 2:
            raise ValueError("ChangeStar requires exactly two temporal observations (T1 and T2).")

        t1_path = file_paths[0]
        t2_path = file_paths[1]
        if not os.path.exists(t1_path) or not os.path.exists(t2_path):
            raise FileNotFoundError(f"Temporal image files missing: '{t1_path}' or '{t2_path}'.")

        cfg = self.get_service_config()
        base_url = cfg.base_url if cfg.is_configured() else settings.CHANGE_MODEL_API_URL

        # 1. Attempt call to microservice if configured
        if base_url and base_url.strip():
            api_url = base_url.rstrip("/")
            path = (cfg.analyze_path or getattr(settings, "CHANGE_MODEL_API_ENDPOINT", "predict") or "predict").lstrip("/")
            timeout = cfg.timeout_seconds if cfg.is_configured() else settings.MODEL_TIMEOUT
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    payload = {"t1_path": t1_path, "t2_path": t2_path, "query": query, "task": task}
                    res = await client.post(f"{api_url}/{path}", json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                        return {
                            "answer": data.get("answer"),
                            "confidence": data.get("confidence"),
                            "evidence": data.get("evidence", {}),
                            "is_simulated": False,
                            "model_latency_ms": latency_ms,
                            "raw_output": data
                        }
            except Exception:
                # Service not reachable, fallback to in-process engine
                pass

        # 2. In-process execution with ChangeStarEngine if weights exist
        weights_path = Path(__file__).resolve().parent.parent.parent / "pretrained_weights" / "changestar1x96_r18_ft_levircd.pth"
        if weights_path.exists():
            try:
                from model_services.changestar_engine import ChangeStarEngine
                engine = ChangeStarEngine.get_instance(str(weights_path))
                result = engine.predict(t1_input=Path(t1_path), t2_input=Path(t2_path), threshold=0.5)

                change_pct = result["change_percentage"]
                if result["changed_pixels"] == 0:
                    answer_text = (
                        f"ChangeStar detected 0.0% changed surface area (0 changed pixels out of {result['total_pixels']} total pixels). "
                        f"No significant structural changes were detected between the two observation epochs at decision threshold 0.5."
                    )
                else:
                    answer_text = (
                        f"ChangeStar detected {change_pct}% changed surface area between temporal observations. "
                        f"Identified {result['changed_pixels']} changed pixels out of {result['total_pixels']} total pixels."
                    )

                # Persist change mask image
                uploads_dir = Path(settings.UPLOAD_DIR)
                uploads_dir.mkdir(parents=True, exist_ok=True)
                mask_filename = f"change_mask_{int(time.time() * 1000)}.png"
                mask_path = uploads_dir / mask_filename

                if "change_mask_base64" in result:
                    mask_raw = result["change_mask_base64"]
                    if "," in mask_raw:
                        mask_raw = mask_raw.split(",")[1]
                    with open(mask_path, "wb") as f:
                        f.write(base64.b64decode(mask_raw))
                    mask_url = f"/api/uploads/{mask_filename}"
                else:
                    mask_url = None

                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "answer": answer_text,
                    "confidence": None,  # Change detection mask does not yield calibrated posterior probability
                    "evidence": {
                        "text": f"LEVIR-CD change detector verified structural changes across {change_pct}% of the surveyed extent.",
                        "change_percentage": change_pct,
                        "change_mask_url": mask_url,
                        "changed_pixels": result["changed_pixels"],
                        "total_pixels": result["total_pixels"]
                    },
                    "is_simulated": False,
                    "model_latency_ms": latency_ms,
                    "raw_output": result
                }
            except Exception as e:
                if not settings.ENABLE_MOCK_FALLBACK_FOR_TESTS:
                    raise RuntimeError(f"ChangeStar local inference failed: {str(e)}")

        # 3. Research mock fallback for tests
        if settings.ENABLE_MOCK_FALLBACK_FOR_TESTS:
            res = await self.mock_fallback.predict(query, file_paths, task, **kwargs)
            res["evidence"]["text"] = f"(ChangeStar microservice offline; verified mock output active.)"
            return res

        raise RuntimeError("ChangeStar specialist model is unavailable. Start microservice on port 8001 or provide valid checkpoint.")
