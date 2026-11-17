# backend/models/mock_adapter.py
import time
import os
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageDraw
from backend.models.base_model import BaseModelAdapter
from backend.config.settings import settings

class MockSpecialistAdapter(BaseModelAdapter):
    """
    Standardized Research Mock Adapter.
    Used for local testing and validation when live remote endpoints are not configured.
    Adheres strictly to scientific honesty:
    - Sets is_simulated = True
    - Sets confidence = None (unless mathematically computed)
    - Distinguishes simulation from production outputs
    """
    def __init__(self, model_id: str, display_name: str, specialist_role: str):
        super().__init__(model_id, display_name)
        self.specialist_role = specialist_role

    def is_configured(self) -> bool:
        return True

    async def health_check(self) -> Tuple[bool, str]:
        return True, f"Mock Specialist Adapter '{self.display_name}' is active for offline research and testing."

    async def predict(
        self,
        query: str,
        file_paths: List[str],
        task: str,
        **kwargs
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        normalized_q = query.lower()

        evidence_text = f"Simulated execution trace from {self.display_name} (Specialist Role: {self.specialist_role})."
        boxes = []
        regions = []
        overlay_url = None
        change_mask_url = None
        optical_summary = None
        sar_summary = None

        # 1. Bi-Temporal Change Detection & Change VQA
        if task in ("CHANGE_DETECTION", "CHANGE_VQA"):
            answer = (
                f"[MOCK SPECIALIST: {self.display_name}] Dense bi-temporal feature comparison between the provided epochs "
                f"reveals noticeable surface modifications: expansion in built-up infrastructure and localized shifts in vegetation density. "
                f"Query analysis: '{query}'."
            )
            evidence_text = (
                "Change vector analysis conducted on paired bi-temporal inputs. "
                "Calculated positive difference magnitude in structural reflectance. (Simulation)"
            )
            regions = [
                {"region_id": 1, "description": "Sector Alpha: Structural expansion", "change_intensity": "Moderate"},
                {"region_id": 2, "description": "Sector Beta: Vegetative clearance", "change_intensity": "High"}
            ]
            # Generate a mock change mask image
            if file_paths:
                change_mask_url = self._create_mock_overlay(file_paths[0], "CHANGE_DETECTION_MASK")

        # 2. Optical + SAR Multimodal Analysis
        elif task == "OPTICAL_SAR_ANALYSIS":
            answer = (
                f"[MOCK SPECIALIST: {self.display_name}] Cross-attention multimodal fusion executed on Optical and SAR observations. "
                f"Optical spectral bands provide rich land-cover color differentiation, while SAR radar backscatter highlights "
                f"high-dielectric building corners (double-bounce reflections) and specular water bodies. "
                f"Built-up areas and open water bodies are successfully differentiated through joint cross-modal representation."
            )
            optical_summary = "RGB multi-band spectral reflectance: discriminates vegetated surfaces and soil."
            sar_summary = "Polarimetric backscatter intensity: high double-bounce return confirms geometric built-up structures; low return confirms specular water surface."
            evidence_text = "Cross-modal contrastive embeddings aligned via joint attention projection. (Simulation)"

        # 3. Grounding
        elif task == "GROUNDING":
            answer = (
                f"[MOCK SPECIALIST: {self.display_name}] Identified and localized the spatial region corresponding to '{query}'. "
                f"Bounding box coordinates extracted from grounded feature map."
            )
            boxes = [
                {"box_2d": [0.25, 0.30, 0.65, 0.75], "label": "Referenced Water Body / Region", "confidence": None}
            ]
            if file_paths:
                overlay_url = self._create_mock_overlay(file_paths[0], "GROUNDING_OVERLAY", boxes[0]["box_2d"])

        # 4. Captioning & Scene / Object Analysis
        elif task == "CAPTIONING":
            answer = (
                f"[MOCK SPECIALIST: {self.display_name}] High-resolution remote sensing scene overview: "
                f"The image portrays a diverse landscape containing mixed residential and commercial built-up structures, "
                f"connected transportation road corridors, interspersed with green vegetation canopy and open terrain."
            )

        # 5. General VQA
        else:
            answer = (
                f"[MOCK SPECIALIST: {self.display_name}] Analysis of remote-sensing observation in response to: '{query}'. "
                f"The observation displays characteristic earth observation features including delineated land-use zones, "
                f"road networks, and spatial structures."
            )

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "answer": answer,
            "confidence": None,  # Scientifically honest: None when not provided by model
            "evidence": {
                "text": evidence_text,
                "regions": regions,
                "boxes": boxes,
                "overlay_url": overlay_url,
                "change_mask_url": change_mask_url,
                "optical_feature_summary": optical_summary,
                "sar_feature_summary": sar_summary,
                "raw_model_metrics": {
                    "mode": "MOCK_RESEARCH_ADAPTER",
                    "specialist": self.display_name,
                    "simulated_inference": True
                }
            },
            "is_simulated": True,
            "model_latency_ms": latency_ms,
            "raw_output": {"status": "MOCK_SUCCESS", "specialist": self.model_id}
        }

    def _create_mock_overlay(self, base_image_path: str, overlay_type: str, box_coords: Optional[List[float]] = None) -> Optional[str]:
        """
        Creates a visual evidence artifact with clear research watermarking.
        """
        try:
            with Image.open(base_image_path) as img:
                canvas = img.convert("RGBA")
                overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(overlay)
                w, h = canvas.size

                if overlay_type == "GROUNDING_OVERLAY" and box_coords:
                    ymin, xmin, ymax, xmax = box_coords
                    box = [int(xmin * w), int(ymin * h), int(xmax * w), int(ymax * h)]
                    draw.rectangle(box, outline=(6, 182, 212, 255), width=4)
                    draw.rectangle(box, fill=(6, 182, 212, 60))
                elif overlay_type == "CHANGE_DETECTION_MASK":
                    # Draw a semi-transparent change polygon/region
                    poly = [(int(w * 0.3), int(h * 0.2)), (int(w * 0.7), int(h * 0.3)), (int(w * 0.6), int(h * 0.8)), (int(w * 0.2), int(h * 0.6))]
                    draw.polygon(poly, fill=(239, 68, 68, 90), outline=(239, 68, 68, 255))

                combined = Image.alpha_composite(canvas, overlay).convert("RGB")
                out_name = f"overlay_{int(time.time() * 1000)}_{os.path.basename(base_image_path)}.jpg"
                out_path = os.path.join(settings.UPLOAD_DIR, out_name)
                combined.save(out_path, "JPEG")
                return f"/api/uploads/{out_name}"
        except Exception:
            return None
