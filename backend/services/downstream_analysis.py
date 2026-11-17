# backend/services/downstream_analysis.py
"""
Downstream Analysis Layer for SatQuery AI.

Provides specialized post-inference analytical processing for specialist models:
1. CROMA:
   - Verifies whether a compatible trained downstream classifier or segmentation head is present.
   - If present, evaluates downstream classes.
   - If absent, explicitly sets semantic_classification_available = False, refuses to invent
     land-cover labels, and exposes verified feature metrics (225 patches, 768-d embeddings,
     GAP norms, and contrastive cosine similarity).
   - Provides clear scientific explanation that cosine similarity reflects vector alignment in
     contrastive latent space rather than physical land-cover percentage or ground-truth change.

2. ChangeStar:
   - Calculates change-mask empirical statistics strictly from the actual binary mask / prob_map.
   - Computes 4-quadrant spatial distribution (Northwest, Northeast, Southwest, Southeast).
   - Computes bounding box [ymin, xmin, ymax, xmax] (normalized [0, 1] and pixel coordinates).
   - Computes spatial centroid (normalized and pixel coordinates).
   - Identifies dominant quadrant(s) and generates spatial clustering summary.
   - Accurately reports zero-change when changed_pixels == 0.

3. GeoChat-7B:
   - Verifies visual question answering and grounded bounding box outputs.
"""

import os
import io
import base64
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
from PIL import Image

logger = logging.getLogger("DownstreamAnalysisLayer")

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class DownstreamAnalysisLayer:
    """
    Universal Downstream Analysis Layer bridging specialist model raw outputs
    and grounded natural-language synthesis.
    """

    @classmethod
    def check_croma_classifier(cls) -> Tuple[bool, Optional[str]]:
        """
        Inspects the workspace for any trained downstream classifier or segmentation head
        compatible with CROMA 768-dimensional embeddings.
        Returns (is_available, checkpoint_path_or_description).
        """
        candidate_paths = [
            BASE_DIR / "pretrained_weights" / "croma_linear_classifier.pt",
            BASE_DIR / "pretrained_weights" / "croma_segmentation_head.pth",
            BASE_DIR / "pretrained_weights" / "croma_classifier.pt",
            BASE_DIR / "checkpoints" / "croma_classifier.pt",
            BASE_DIR / "models" / "croma_classifier.pt"
        ]

        for p in candidate_paths:
            if p.exists() and p.stat().st_size > 1000:
                logger.info(f"Found compatible CROMA downstream classifier head at {p}")
                return True, str(p)

        return False, None

    @classmethod
    def analyze_croma(
        cls,
        raw_output: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """
        Performs downstream analysis on CROMA multimodal representation outputs.
        """
        classifier_available, classifier_head = cls.check_croma_classifier()

        # Extract feature shapes and metrics from raw_output
        feature_shapes = raw_output.get("feature_shapes", {})
        metrics = raw_output.get("metrics", {})

        embedding_dim = feature_shapes.get("embedding_dim", 768)
        num_patches = feature_shapes.get("num_patches", 225)
        patch_grid = "15x15" if num_patches == 225 else f"{num_patches} patches"

        # Cosine similarity metrics
        cos_sim = metrics.get(
            "sar_optical_cosine_similarity",
            raw_output.get("cosine_similarity", 0.0)
        )
        sar_joint_sim = metrics.get("sar_joint_cosine_similarity")
        opt_joint_sim = metrics.get("optical_joint_cosine_similarity")

        # Vector L2 norms
        sar_norm = metrics.get("sar_gap_l2_norm")
        opt_norm = metrics.get("optical_gap_l2_norm")
        joint_norm = metrics.get("joint_gap_l2_norm")

        similarity_explanation = (
            f"Cosine similarity ({cos_sim:.4f}) measures the angular orientation between normalized "
            f"768-dimensional Sentinel-1 SAR and Sentinel-2 optical global feature vectors within "
            f"CROMA's shared multimodal contrastive latent space. It indicates how closely polarimetric "
            f"radar backscatter patterns align with multispectral reflectance in the embedding manifold. "
            f"It is not an empirical metric of land-cover category or physical change."
        )

        if not classifier_available:
            labeling_status = (
                "Semantic land-cover classification is unavailable. CROMA operates as an unsupervised "
                "foundation representation model, and no trained downstream classification head is installed. "
                "Categorical labels (e.g., urban, water, forest, cropland) cannot be asserted without a validated classifier."
            )
        else:
            labeling_status = f"Downstream classifier head active ({classifier_head})."

        findings = {
            "task": "OPTICAL_SAR_ANALYSIS",
            "model_name": "CROMA Base",
            "semantic_classification_available": classifier_available,
            "classifier_head": classifier_head,
            "embedding_dim": embedding_dim,
            "num_spatial_patches": num_patches,
            "patch_grid": patch_grid,
            "metrics": {
                "sar_optical_cosine_similarity": round(float(cos_sim), 4),
                "sar_joint_cosine_similarity": round(float(sar_joint_sim), 4) if sar_joint_sim is not None else None,
                "optical_joint_cosine_similarity": round(float(opt_joint_sim), 4) if opt_joint_sim is not None else None,
                "sar_gap_l2_norm": round(float(sar_norm), 4) if sar_norm is not None else None,
                "optical_gap_l2_norm": round(float(opt_norm), 4) if opt_norm is not None else None,
                "joint_gap_l2_norm": round(float(joint_norm), 4) if joint_norm is not None else None,
            },
            "similarity_interpretation": similarity_explanation,
            "semantic_labeling_status": labeling_status,
            "findings_summary": (
                f"Extracted {embedding_dim}-dimensional joint multimodal representation across {num_patches} patches ({patch_grid}). "
                f"Cross-modal radar-optical cosine alignment: {cos_sim:.4f}. "
                f"{labeling_status}"
            )
        }
        return findings

    @classmethod
    def _extract_mask_array(
        cls,
        raw_output: Dict[str, Any],
        mask_path: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """
        Helper to decode and extract a 2D uint8/bool numpy mask array from various representations:
        1. Direct numpy array in raw_output
        2. Base64 encoded PNG in raw_output['change_mask_base64']
        3. Image file on disk at mask_path or raw_output['change_mask_url']
        """
        # 1. Direct numpy array
        if "binary_mask" in raw_output and isinstance(raw_output["binary_mask"], np.ndarray):
            arr = raw_output["binary_mask"]
            return (arr > 0).astype(np.uint8) if arr.ndim == 2 else (arr[:, :, 0] > 0).astype(np.uint8)

        # 2. Base64 encoded PNG
        b64_str = raw_output.get("change_mask_base64")
        if b64_str:
            try:
                if "," in b64_str:
                    b64_str = b64_str.split(",")[1]
                png_bytes = base64.b64decode(b64_str)
                img = Image.open(io.BytesIO(png_bytes)).convert("L")
                arr = np.array(img, dtype=np.uint8)
                return (arr >= 128).astype(np.uint8)
            except Exception as e:
                logger.warning(f"Failed to decode change_mask_base64: {e}")

        # 3. File path on disk
        target_path = mask_path or raw_output.get("change_mask_path")
        if not target_path and "change_mask_url" in raw_output:
            url = raw_output["change_mask_url"]
            if url.startswith("/api/uploads/"):
                fname = url.replace("/api/uploads/", "")
                cand = BASE_DIR / "uploads" / fname
                if cand.exists():
                    target_path = str(cand)

        if target_path and os.path.exists(target_path):
            try:
                img = Image.open(target_path).convert("L")
                arr = np.array(img, dtype=np.uint8)
                return (arr >= 128).astype(np.uint8)
            except Exception as e:
                logger.warning(f"Failed to load change mask from {target_path}: {e}")

        return None

    @classmethod
    def compute_spatial_quadrants(
        cls,
        mask: np.ndarray,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Computes 4-quadrant spatial distribution, bounding box, centroid,
        and spatial clustering summary strictly from the 2D binary change mask.
        """
        h, w = mask.shape[:2]
        total_pixels = int(mask.size)
        changed_pixels = int(np.count_nonzero(mask > 0))
        change_pct = round((changed_pixels / total_pixels) * 100.0, 4) if total_pixels > 0 else 0.0

        mid_y = h // 2
        mid_x = w // 2

        # 4 Quadrants
        quadrant_slices = {
            "Northwest": mask[:mid_y, :mid_x],
            "Northeast": mask[:mid_y, mid_x:],
            "Southwest": mask[mid_y:, :mid_x],
            "Southeast": mask[mid_y:, mid_x:]
        }

        quadrants = []
        dominant_quadrant = None
        max_q_count = -1

        for name, submask in quadrant_slices.items():
            q_total = int(submask.size)
            q_changed = int(np.count_nonzero(submask > 0))
            q_change_pct = round((q_changed / q_total) * 100.0, 4) if q_total > 0 else 0.0
            pct_of_total = round((q_changed / changed_pixels) * 100.0, 2) if changed_pixels > 0 else 0.0

            if q_changed > max_q_count:
                max_q_count = q_changed
                dominant_quadrant = name

            quadrants.append({
                "name": name,
                "changed_pixels": q_changed,
                "total_pixels": q_total,
                "quadrant_change_percentage": q_change_pct,
                "percentage_of_total_change": pct_of_total
            })

        # Bounding box and centroid
        bbox_pixels = None
        bbox_norm = None
        centroid_pixels = None
        centroid_norm = None

        if changed_pixels > 0:
            ys, xs = np.nonzero(mask > 0)
            ymin, ymax = int(np.min(ys)), int(np.max(ys))
            xmin, xmax = int(np.min(xs)), int(np.max(xs))
            bbox_pixels = [ymin, xmin, ymax, xmax]
            bbox_norm = [
                round(ymin / h, 4),
                round(xmin / w, 4),
                round(ymax / h, 4),
                round(xmax / w, 4)
            ]

            cy = float(np.mean(ys))
            cx = float(np.mean(xs))
            centroid_pixels = [round(cy, 1), round(cx, 1)]
            centroid_norm = [round(cy / h, 4), round(cx / w, 4)]

            # Formulate spatial summary
            dom_item = next((q for q in quadrants if q["name"] == dominant_quadrant), None)
            dom_pct = dom_item["percentage_of_total_change"] if dom_item else 0.0

            if dom_pct >= 50.0:
                spatial_summary = (
                    f"Structural changes are predominantly concentrated in the {dominant_quadrant} quadrant "
                    f"({dom_pct}% of total detected change area)."
                )
            elif dom_pct >= 35.0:
                sorted_q = sorted(quadrants, key=lambda x: x["percentage_of_total_change"], reverse=True)
                top2 = f"{sorted_q[0]['name']} ({sorted_q[0]['percentage_of_total_change']}%) and {sorted_q[1]['name']} ({sorted_q[1]['percentage_of_total_change']}%)"
                spatial_summary = f"Structural changes are distributed primarily across the {top2} quadrants."
            else:
                spatial_summary = (
                    "Structural changes are dispersed across multiple quadrants without strong localized concentration."
                )
        else:
            dominant_quadrant = None
            spatial_summary = (
                f"No structural changes detected across any of the four quadrants at decision threshold {threshold}."
            )

        return {
            "total_changed_pixels": changed_pixels,
            "total_pixels": total_pixels,
            "change_percentage": change_pct,
            "quadrants": quadrants,
            "bounding_box": bbox_norm,
            "bounding_box_pixels": bbox_pixels,
            "centroid": centroid_norm,
            "centroid_pixels": centroid_pixels,
            "dominant_quadrant": dominant_quadrant,
            "summary": spatial_summary
        }

    @classmethod
    def analyze_changestar(
        cls,
        raw_output: Dict[str, Any],
        query: str,
        mask_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Performs downstream analysis on ChangeStar change detection outputs.
        Extracts empirical change-mask statistics and spatial quadrant distribution.
        """
        threshold = raw_output.get("threshold", 0.5)
        changed_px = raw_output.get("changed_pixels", 0)
        total_px = raw_output.get("total_pixels", 0)
        change_pct = raw_output.get("change_percentage", 0.0)

        # Attempt to decode full 2D mask for quadrant decomposition
        mask_arr = cls._extract_mask_array(raw_output, mask_path=mask_path)

        if mask_arr is not None:
            spatial_dist = cls.compute_spatial_quadrants(mask_arr, threshold=threshold)
        else:
            # Mask array was unavailable; fallback to overall metrics without fabricating quadrant counts
            spatial_dist = {
                "total_changed_pixels": changed_px,
                "total_pixels": total_px,
                "change_percentage": change_pct,
                "quadrants": [],
                "bounding_box": None,
                "bounding_box_pixels": None,
                "centroid": None,
                "centroid_pixels": None,
                "dominant_quadrant": None,
                "summary": (
                    f"Bi-temporal change detection evaluated {change_pct}% changed surface area "
                    f"({changed_px:,} changed pixels out of {total_px:,} total pixels). "
                    f"Quadrant-level raster decomposition is unavailable."
                )
            }

        findings_summary = (
            f"Evaluated bi-temporal change mask at threshold {threshold}: "
            f"{spatial_dist['change_percentage']}% coverage ({spatial_dist['total_changed_pixels']:,} changed pixels). "
            f"{spatial_dist['summary']}"
        )

        return {
            "task": "CHANGE_DETECTION",
            "model_name": "ChangeStar-1x96 (ResNet-18, LEVIR-CD)",
            "semantic_classification_available": False,  # ChangeStar is a binary change detector, not a semantic classifier
            "spatial_distribution": spatial_dist,
            "metrics": {
                "threshold": threshold,
                "total_pixels": total_px,
                "changed_pixels": changed_px,
                "change_percentage": change_pct,
                "mean_change_probability": raw_output.get("mean_change_probability"),
                "max_change_probability": raw_output.get("max_change_probability")
            },
            "findings_summary": findings_summary
        }

    @classmethod
    def analyze_geochat(
        cls,
        raw_output: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """
        Performs downstream analysis on GeoChat-7B vision-language model outputs.
        """
        evidence = raw_output.get("evidence", {})
        boxes = evidence.get("boxes", [])
        regions = evidence.get("regions", [])

        return {
            "task": "VQA",
            "model_name": "GeoChat-7B",
            "semantic_classification_available": True,  # VLM generates open-vocabulary natural language
            "has_visual_grounding": len(boxes) > 0,
            "grounded_boxes_count": len(boxes),
            "regions_count": len(regions),
            "metrics": {
                "grounded_boxes": len(boxes),
                "referenced_regions": len(regions)
            },
            "findings_summary": (
                f"GeoChat-7B generated vision-language interpretation with "
                f"{len(boxes)} grounded bounding box(es) and {len(regions)} sector reference(s)."
            )
        }

    @classmethod
    def analyze(
        cls,
        task: str,
        model_name: str,
        model_output: Dict[str, Any],
        query: str,
        mask_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Universal entry point to analyze specialist outputs.
        """
        norm_task = (task or "").upper()
        norm_model = (model_name or "").lower()

        raw_output = model_output.get("raw_output") or model_output

        if "croma" in norm_model or "OPTICAL_SAR" in norm_task:
            return cls.analyze_croma(raw_output=raw_output, query=query)
        elif "change" in norm_model or "CHANGE" in norm_task:
            return cls.analyze_changestar(raw_output=raw_output, query=query, mask_path=mask_path)
        elif "geochat" in norm_model or norm_task in ("VQA", "CAPTIONING", "SCENE_ANALYSIS"):
            return cls.analyze_geochat(raw_output=raw_output, query=query)
        else:
            return {
                "task": norm_task,
                "model_name": model_name,
                "semantic_classification_available": False,
                "metrics": {},
                "findings_summary": f"Inference completed by {model_name}."
            }

