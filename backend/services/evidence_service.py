# backend/services/evidence_service.py
from typing import Dict, Any, Optional, List
from backend.router.schemas import Evidence, BoundingBox

class EvidenceService:
    @staticmethod
    def normalize_evidence(
        raw_evidence: Optional[Dict[str, Any]],
        task: str,
        supports_grounding: bool,
        supports_change_maps: bool
    ) -> Evidence:
        """
        Normalizes and validates evidence outputs from specialist models.
        Strictly prevents evidence fabrication.
        """
        if not raw_evidence:
            raw_evidence = {}

        raw_boxes = raw_evidence.get("boxes", [])
        parsed_boxes: List[BoundingBox] = []
        for b in raw_boxes:
            if isinstance(b, dict) and "box_2d" in b:
                parsed_boxes.append(
                    BoundingBox(
                        box_2d=b["box_2d"],
                        label=b.get("label", "Detected Feature"),
                        confidence=b.get("confidence")
                    )
                )

        text_evidence = raw_evidence.get("text")
        if not text_evidence:
            text_evidence = "Specific analytical features identified during model inference."

        regions = raw_evidence.get("regions", [])
        overlay_url = raw_evidence.get("overlay_url")
        change_mask_url = raw_evidence.get("change_mask_url")
        change_pct = raw_evidence.get("change_percentage")
        changed_pixels = raw_evidence.get("changed_pixels")
        total_pixels = raw_evidence.get("total_pixels")

        optical_summary = raw_evidence.get("optical_feature_summary")
        if isinstance(optical_summary, dict):
            optical_summary = ", ".join(f"{k}: {v}" for k, v in optical_summary.items())
        elif optical_summary is not None:
            optical_summary = str(optical_summary)

        sar_summary = raw_evidence.get("sar_feature_summary")
        if isinstance(sar_summary, dict):
            sar_summary = ", ".join(f"{k}: {v}" for k, v in sar_summary.items())
        elif sar_summary is not None:
            sar_summary = str(sar_summary)

        spatial_distribution = raw_evidence.get("spatial_distribution")
        downstream_findings = raw_evidence.get("downstream_findings")

        return Evidence(
            text=text_evidence,
            regions=regions,
            boxes=parsed_boxes,
            overlay_url=overlay_url,
            change_mask_url=change_mask_url,
            change_percentage=change_pct,
            changed_pixels=changed_pixels,
            total_pixels=total_pixels,
            optical_feature_summary=optical_summary,
            sar_feature_summary=sar_summary,
            raw_model_metrics=raw_evidence.get("raw_model_metrics"),
            spatial_distribution=spatial_distribution,
            downstream_findings=downstream_findings
        )
