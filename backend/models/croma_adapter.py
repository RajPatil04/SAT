# backend/models/croma_adapter.py
import time
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import httpx

from backend.models.base_model import BaseModelAdapter
from backend.models.mock_adapter import MockSpecialistAdapter
from backend.config.endpoint_config import CentralConfigManager, ServiceConfig
from backend.config.settings import settings
from backend.preprocessing.croma_preprocessor import CROMAPreprocessor

class CROMAAdapter(BaseModelAdapter):
    """
    Dedicated Adapter for CROMA (Contrastive Radar-Optical Masked Autoencoders).
    NeurIPS 2023 Foundation Model for Joint Sentinel-1 SAR + Sentinel-2 Optical representation.
    Section 3: Authoritative configuration via model_endpoints.yaml.
    """
    def __init__(self):
        super().__init__("croma", "CROMA")
        self.preprocessor = CROMAPreprocessor()
        self.mock_fallback = MockSpecialistAdapter("croma", "CROMA", "Multimodal Optical-SAR Specialist")

    def get_service_config(self) -> ServiceConfig:
        return CentralConfigManager.get_config().get_service("croma")

    def is_configured(self) -> bool:
        cfg = self.get_service_config()
        if cfg.is_configured():
            return True
        if settings.CROMA_API_URL and settings.CROMA_API_URL.strip():
            return True
        weights_path = Path(__file__).resolve().parent.parent.parent / "pretrained_weights" / "CROMA_base.pt"
        return weights_path.exists()

    async def health_check(self) -> Tuple[bool, str]:
        cfg = self.get_service_config()
        base_url = cfg.base_url if cfg.is_configured() else settings.CROMA_API_URL

        # 1. Microservice check
        if base_url and base_url.strip():
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    res = await client.get(f"{base_url.rstrip('/')}/health")
                    if res.status_code == 200:
                        data = res.json()
                        return True, f"CROMA microservice ONLINE at {base_url} ({data.get('device', 'cpu')})."
            except Exception:
                pass

        # 2. Local checkpoint check
        weights_path = Path(__file__).resolve().parent.parent.parent / "pretrained_weights" / "CROMA_base.pt"
        if weights_path.exists():
            return True, f"CROMA weights available locally ({weights_path.stat().st_size / (1024*1024):.1f} MB). Ready for in-process inference."

        if settings.ENABLE_MOCK_FALLBACK_FOR_TESTS:
            return True, "CROMA operating in MOCK mode (no weights or microservice configured)."

        return False, "CROMA is unconfigured: microservice offline and pretrained weights not found."

    async def predict(
        self,
        query: str,
        file_paths: List[str],
        task: str,
        **kwargs
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        if len(file_paths) < 2:
            raise ValueError("CROMA requires paired multimodal inputs (Optical image/array and SAR image/array).")

        # Preprocess / identify optical and SAR assets
        prep_data = self.preprocessor.preprocess(file_paths)
        optical_path = prep_data["optical_path"]
        sar_path = prep_data["sar_path"]

        cfg = self.get_service_config()
        base_url = cfg.base_url if cfg.is_configured() else settings.CROMA_API_URL

        # 1. Call microservice if configured
        if base_url and base_url.strip():
            api_url = base_url.rstrip("/")
            path = (cfg.analyze_path or getattr(settings, "CROMA_API_ENDPOINT", "predict") or "predict").lstrip("/")
            timeout = cfg.timeout_seconds if cfg.is_configured() else settings.MODEL_TIMEOUT
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    payload = {
                        "optical_path": optical_path,
                        "sar_path": sar_path,
                        "query": query,
                        "task": task
                    }
                    res = await client.post(f"{api_url}/{path}", json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                        return {
                            "answer": data.get("answer"),
                            "confidence": None,  # Feature extractor does not yield calibrated probability
                            "evidence": data.get("evidence", {}),
                            "is_simulated": False,
                            "model_latency_ms": latency_ms,
                            "raw_output": data
                        }
            except Exception:
                pass

        # 2. In-process execution with CROMAEngine if weights exist
        weights_path = Path(__file__).resolve().parent.parent.parent / "pretrained_weights" / "CROMA_base.pt"
        if weights_path.exists():
            try:
                from model_services.croma_engine import CROMAEngine
                engine = CROMAEngine.get_instance(str(weights_path))
                result = engine.predict(sar_input=Path(sar_path), optical_input=Path(optical_path), serialize_vectors=False)

                shapes = result.get("feature_shapes", {})
                metrics = result.get("metrics", {})
                sim = metrics.get("sar_optical_cosine_similarity", 0.0)

                answer_text = (
                    f"CROMA Optical–SAR cross-attention feature extraction executed. "
                    f"Extracted {shapes.get('embedding_dim', 768)}-dimensional joint multimodal representation across {shapes.get('num_patches', 225)} spatial patches. "
                    f"Cosine similarity between SAR radar backscatter and optical spectral features: {sim:.4f}. "
                    f"Downstream task heads are required for specific categorical land-cover labeling."
                )

                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "answer": answer_text,
                    "confidence": None,
                    "evidence": {
                        "text": f"CROMA Base foundation model extracted cross-attention embeddings (768-d GAP, {shapes.get('num_patches', 225)} patches).",
                        "optical_feature_summary": f"Optical GAP Vector (Dim: {shapes.get('embedding_dim', 768)}), Patches: {shapes.get('num_patches', 225)}",
                        "sar_feature_summary": f"SAR GAP Vector (Dim: {shapes.get('embedding_dim', 768)}), Polarimetric Radar Backscatter",
                        "cosine_similarity": sim,
                        "raw_model_metrics": metrics
                    },
                    "is_simulated": False,
                    "model_latency_ms": latency_ms,
                    "raw_output": result
                }
            except Exception as e:
                if not settings.ENABLE_MOCK_FALLBACK_FOR_TESTS:
                    raise RuntimeError(f"CROMA local inference failed: {str(e)}")

        # 3. Mock fallback for test suite
        if settings.ENABLE_MOCK_FALLBACK_FOR_TESTS:
            res = await self.mock_fallback.predict(query, file_paths, task, **kwargs)
            res["evidence"]["text"] = "(CROMA microservice offline; verified mock output active.)"
            return res

        raise RuntimeError("CROMA specialist model is unavailable. Start microservice on port 8002 or provide valid checkpoint.")
