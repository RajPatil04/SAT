# backend/tests/test_language_generation.py
import asyncio
import pytest
from backend.services.language_generation_service import (
    LanguageGenerationService,
    DeterministicAnswerSynthesizer
)


def test_changestar_language_generation_with_change():
    """
    Verifies that ChangeStar language generation produces a structured, readable answer
    reporting the change percentage, spatial quadrant distribution, and structural context.
    """
    query = "What changes occurred between these two satellite observations? Were any buildings built?"
    findings = {
        "task": "CHANGE_DETECTION",
        "model_name": "ChangeStar-1x96 (ResNet-18, LEVIR-CD)",
        "semantic_classification_available": False,
        "spatial_distribution": {
            "total_pixels": 65536,
            "total_changed_pixels": 3200,
            "change_percentage": 4.88,
            "dominant_quadrant": "Northwest",
            "quadrants": [
                {"name": "Northwest", "changed_pixels": 2400, "total_pixels": 16384, "quadrant_change_percentage": 14.65, "percentage_of_total_change": 75.0},
                {"name": "Northeast", "changed_pixels": 800, "total_pixels": 16384, "quadrant_change_percentage": 4.88, "percentage_of_total_change": 25.0},
                {"name": "Southwest", "changed_pixels": 0, "total_pixels": 16384, "quadrant_change_percentage": 0.0, "percentage_of_total_change": 0.0},
                {"name": "Southeast", "changed_pixels": 0, "total_pixels": 16384, "quadrant_change_percentage": 0.0, "percentage_of_total_change": 0.0}
            ],
            "bounding_box": [0.05, 0.05, 0.45, 0.65],
            "summary": "Structural changes are predominantly concentrated in the Northwest quadrant (75.0% of total detected change area)."
        },
        "metrics": {"threshold": 0.50}
    }

    raw_output = {
        "changed_pixels": 3200,
        "total_pixels": 65536,
        "change_percentage": 4.88
    }

    answer = asyncio.run(
        LanguageGenerationService.generate_grounded_answer(
            query=query,
            task="CHANGE_DETECTION",
            model_name="ChangeStar",
            model_output=raw_output,
            downstream_findings=findings
        )
    )

    assert "4.88%" in answer
    assert "3,200 changed pixels" in answer
    assert "Northwest" in answer
    assert "75.0%" in answer
    assert "Structural Context" in answer
    assert "ChangeStar-1x96" in answer
    assert "LEVIR-CD" in answer


def test_changestar_language_generation_zero_change():
    """
    Verifies that ChangeStar language generation accurately reports zero change.
    """
    query = "Is there any change in this area?"
    findings = {
        "task": "CHANGE_DETECTION",
        "model_name": "ChangeStar-1x96 (ResNet-18, LEVIR-CD)",
        "semantic_classification_available": False,
        "spatial_distribution": {
            "total_pixels": 65536,
            "total_changed_pixels": 0,
            "change_percentage": 0.0,
            "dominant_quadrant": None,
            "quadrants": [],
            "bounding_box": None,
            "summary": "No structural changes detected across any of the four quadrants at decision threshold 0.5."
        },
        "metrics": {"threshold": 0.50}
    }

    raw_output = {
        "changed_pixels": 0,
        "total_pixels": 65536,
        "change_percentage": 0.0
    }

    answer = asyncio.run(
        LanguageGenerationService.generate_grounded_answer(
            query=query,
            task="CHANGE_DETECTION",
            model_name="ChangeStar",
            model_output=raw_output,
            downstream_findings=findings
        )
    )

    assert "no significant structural changes" in answer.lower()
    assert "0.0%" in answer


def test_croma_language_generation():
    """
    Verifies that CROMA language generation produces a structured answer explaining
    the 768-d joint representations, 225 spatial patches, cosine similarity meaning,
    and explicitly refusing to fabricate land-cover labels.
    """
    query = "What is the land cover and how do the optical and SAR features align?"
    findings = {
        "task": "OPTICAL_SAR_ANALYSIS",
        "model_name": "CROMA Base",
        "semantic_classification_available": False,
        "embedding_dim": 768,
        "num_spatial_patches": 225,
        "patch_grid": "15x15",
        "metrics": {
            "sar_optical_cosine_similarity": 0.8145,
            "sar_joint_cosine_similarity": 0.9120,
            "optical_joint_cosine_similarity": 0.9340,
            "sar_gap_l2_norm": 13.5,
            "optical_gap_l2_norm": 15.2,
            "joint_gap_l2_norm": 19.1
        }
    }

    raw_output = {
        "feature_shapes": {"num_patches": 225, "embedding_dim": 768},
        "metrics": findings["metrics"]
    }

    answer = asyncio.run(
        LanguageGenerationService.generate_grounded_answer(
            query=query,
            task="OPTICAL_SAR_ANALYSIS",
            model_name="CROMA",
            model_output=raw_output,
            downstream_findings=findings
        )
    )

    assert "768-dimensional joint multimodal representations" in answer
    assert "225 spatial patches" in answer
    assert "0.8145" in answer
    assert "Cross-Modal Alignment Interpretation" in answer
    assert "angular orientation" in answer
    assert "empirical measure of surface change" in answer
    assert "Semantic Land-Cover Classification Status" in answer
    assert "unavailable" in answer.lower()
    assert "unsupervised" in answer.lower()
    assert "CROMA Base (NeurIPS 2023)" in answer


def test_query_vegetation_intent():
    """
    Verifies that questions inquiring about vegetation receive relevant vegetation context
    without hallucinating crop types.
    """
    query = "Did the forest and vegetation change?"
    findings = {
        "task": "CHANGE_DETECTION",
        "model_name": "ChangeStar",
        "semantic_classification_available": False,
        "spatial_distribution": {
            "total_pixels": 10000,
            "total_changed_pixels": 500,
            "change_percentage": 5.0,
            "dominant_quadrant": "Southwest",
            "quadrants": [
                {"name": "Southwest", "changed_pixels": 500, "total_pixels": 2500, "quadrant_change_percentage": 20.0, "percentage_of_total_change": 100.0}
            ],
            "bounding_box": [0.5, 0.0, 0.9, 0.4],
            "summary": "Concentrated in Southwest quadrant."
        },
        "metrics": {"threshold": 0.50}
    }

    raw_output = {"changed_pixels": 500, "total_pixels": 10000, "change_percentage": 5.0}

    answer = asyncio.run(
        LanguageGenerationService.generate_grounded_answer(
            query=query,
            task="CHANGE_DETECTION",
            model_name="ChangeStar",
            model_output=raw_output,
            downstream_findings=findings
        )
    )

    assert "Vegetation Context" in answer
    assert "NDVI" in answer