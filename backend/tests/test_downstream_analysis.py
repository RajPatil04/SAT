# backend/tests/test_downstream_analysis.py
import io
import base64
import numpy as np
import pytest
from PIL import Image

from backend.services.downstream_analysis import DownstreamAnalysisLayer


def test_croma_downstream_no_classifier():
    """
    Verifies that when no classifier head exists:
    - semantic_classification_available is False
    - Technical metrics (768-d embeddings, 225 patches, cosine similarity) are reported
    - Clear explanation of cosine similarity is provided without fabricating land-cover classes
    """
    is_avail, head = DownstreamAnalysisLayer.check_croma_classifier()
    assert is_avail is False
    assert head is None

    raw_output = {
        "feature_shapes": {
            "num_patches": 225,
            "embedding_dim": 768
        },
        "metrics": {
            "sar_optical_cosine_similarity": 0.7421,
            "sar_joint_cosine_similarity": 0.8812,
            "optical_joint_cosine_similarity": 0.8934,
            "sar_gap_l2_norm": 12.5,
            "optical_gap_l2_norm": 14.1,
            "joint_gap_l2_norm": 16.8
        }
    }

    findings = DownstreamAnalysisLayer.analyze_croma(raw_output, "What land cover is visible?")
    assert findings["task"] == "OPTICAL_SAR_ANALYSIS"
    assert findings["semantic_classification_available"] is False
    assert findings["num_spatial_patches"] == 225
    assert findings["embedding_dim"] == 768
    assert findings["patch_grid"] == "15x15"
    assert findings["metrics"]["sar_optical_cosine_similarity"] == 0.7421
    assert "angular orientation" in findings["similarity_interpretation"]
    assert "not an empirical metric of land-cover category" in findings["similarity_interpretation"]
    assert "Semantic land-cover classification is unavailable" in findings["semantic_labeling_status"]


def test_changestar_quadrant_calculation_synthetic():
    """
    Tests spatial quadrant calculation on a synthetic mask with known localized change.
    """
    # 100 x 100 mask with 400 changed pixels in top-left (NW)
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[10:30, 10:30] = 255  # 20 * 20 = 400 pixels

    spatial = DownstreamAnalysisLayer.compute_spatial_quadrants(mask, threshold=0.50)
    assert spatial["total_changed_pixels"] == 400
    assert spatial["total_pixels"] == 10000
    assert spatial["change_percentage"] == 4.0
    assert spatial["dominant_quadrant"] == "Northwest"

    nw_item = next(q for q in spatial["quadrants"] if q["name"] == "Northwest")
    assert nw_item["changed_pixels"] == 400
    assert nw_item["percentage_of_total_change"] == 100.0

    ne_item = next(q for q in spatial["quadrants"] if q["name"] == "Northeast")
    assert ne_item["changed_pixels"] == 0
    assert ne_item["percentage_of_total_change"] == 0.0

    assert spatial["bounding_box"] == [0.1, 0.1, 0.29, 0.29]
    assert spatial["centroid"] == [0.195, 0.195]
    assert "predominantly concentrated in the Northwest quadrant" in spatial["summary"]


def test_changestar_zero_change():
    """
    Tests spatial analysis when zero change is detected.
    """
    mask = np.zeros((100, 100), dtype=np.uint8)
    spatial = DownstreamAnalysisLayer.compute_spatial_quadrants(mask, threshold=0.50)

    assert spatial["total_changed_pixels"] == 0
    assert spatial["change_percentage"] == 0.0
    assert spatial["dominant_quadrant"] is None
    assert spatial["bounding_box"] is None
    assert spatial["centroid"] is None
    assert "No structural changes detected" in spatial["summary"]


def test_changestar_multi_quadrant():
    """
    Tests spatial analysis with distributed changes across multiple quadrants.
    """
    mask = np.zeros((100, 100), dtype=np.uint8)
    # NW: 300 pixels
    mask[10:25, 10:30] = 255  # 15 * 20 = 300
    # NE: 100 pixels
    mask[10:20, 60:70] = 255  # 10 * 10 = 100

    spatial = DownstreamAnalysisLayer.compute_spatial_quadrants(mask, threshold=0.50)
    assert spatial["total_changed_pixels"] == 400
    assert spatial["dominant_quadrant"] == "Northwest"

    nw = next(q for q in spatial["quadrants"] if q["name"] == "Northwest")
    ne = next(q for q in spatial["quadrants"] if q["name"] == "Northeast")
    assert nw["percentage_of_total_change"] == 75.0
    assert ne["percentage_of_total_change"] == 25.0


def test_changestar_base64_mask_decoding():
    """
    Tests decoding base64-encoded PNG change mask in analyze_changestar.
    """
    mask_arr = np.zeros((64, 64), dtype=np.uint8)
    mask_arr[32:48, 32:48] = 255  # SE quadrant: 16 * 16 = 256 pixels

    pil_img = Image.fromarray(mask_arr, mode="L")
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    b64_str = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

    raw_output = {
        "threshold": 0.50,
        "total_pixels": 4096,
        "changed_pixels": 256,
        "change_percentage": 6.25,
        "change_mask_base64": b64_str
    }

    findings = DownstreamAnalysisLayer.analyze_changestar(raw_output, "Did the surface change?")
    assert findings["task"] == "CHANGE_DETECTION"
    spatial = findings["spatial_distribution"]
    assert spatial["total_changed_pixels"] == 256
    assert spatial["dominant_quadrant"] == "Southeast"
    assert "Southeast" in spatial["summary"]

