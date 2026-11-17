# backend/tests/test_router.py
import pytest
from backend.router.schemas import TaskType, InputType, ModalityType, CompatibilityResult, ImageMetadata
from backend.router.routing_engine import RoutingEngine
from backend.router.query_analyzer import QueryAnalyzer
from backend.router.task_classifier import TaskClassifier

from backend.config.settings import settings

def make_meta(filename: str, modality: ModalityType = ModalityType.OPTICAL, w: int = 512, h: int = 512):
    return ImageMetadata(
        filename=filename,
        format="PNG",
        width=w,
        height=h,
        channels=3 if modality != ModalityType.SAR else 1,
        datatype="RGB",
        detected_modality=modality
    )

def test_case_1_single_optical_vqa(monkeypatch):
    """CASE 1: Single optical image + 'Describe this image.' -> VQA/CAPTIONING -> GeoChat"""
    monkeypatch.setattr(settings, "ENABLE_MOCK_FALLBACK_FOR_TESTS", True)
    meta = [make_meta("scene.png", ModalityType.OPTICAL)]
    comp = CompatibilityResult(is_compatible=True, input_type=InputType.SINGLE_IMAGE, modality=ModalityType.OPTICAL)
    
    decision = RoutingEngine.route(
        query="Describe this image.",
        images_metadata=meta,
        compatibility=comp
    )

    assert decision.is_executable is True
    assert decision.detected_task in (TaskType.CAPTIONING, TaskType.VQA)
    assert decision.detected_input_type == InputType.SINGLE_IMAGE
    assert decision.selected_model_id == "geochat-7b"

def test_case_2_single_image_grounding(monkeypatch):
    """CASE 2: Single image + 'Highlight the water body.' -> GROUNDING -> Grounding specialist or GeoChat"""
    monkeypatch.setattr(settings, "ENABLE_MOCK_FALLBACK_FOR_TESTS", True)
    meta = [make_meta("coastal.png", ModalityType.OPTICAL)]
    comp = CompatibilityResult(is_compatible=True, input_type=InputType.SINGLE_IMAGE, modality=ModalityType.OPTICAL)

    decision = RoutingEngine.route(
        query="Highlight the water body.",
        images_metadata=meta,
        compatibility=comp
    )

    assert decision.is_executable is True
    assert decision.detected_task == TaskType.GROUNDING
    assert decision.selected_model_id in ("geochat-7b", "grounding-specialist")

def test_case_3_bitemporal_change_detection():
    """CASE 3: Two temporal images + 'What changed?' -> CHANGE_DETECTION -> ChangeStar"""
    meta = [make_meta("t1.png", ModalityType.OPTICAL), make_meta("t2.png", ModalityType.OPTICAL)]
    comp = CompatibilityResult(is_compatible=True, input_type=InputType.BI_TEMPORAL, modality=ModalityType.OPTICAL)

    decision = RoutingEngine.route(
        query="What changed between these two dates?",
        images_metadata=meta,
        compatibility=comp
    )

    assert decision.is_executable is True
    assert decision.detected_task == TaskType.CHANGE_DETECTION
    assert decision.detected_input_type == InputType.BI_TEMPORAL
    assert decision.selected_model_id == "changestar"

def test_case_4_bitemporal_change_vqa():
    """CASE 4: Two temporal images + 'Has the built-up area increased?' -> CHANGE_VQA -> ChangeStar"""
    meta = [make_meta("t1.png", ModalityType.OPTICAL), make_meta("t2.png", ModalityType.OPTICAL)]
    comp = CompatibilityResult(is_compatible=True, input_type=InputType.BI_TEMPORAL, modality=ModalityType.OPTICAL)

    decision = RoutingEngine.route(
        query="Has the built-up area increased?",
        images_metadata=meta,
        compatibility=comp
    )

    assert decision.is_executable is True
    assert decision.detected_task == TaskType.CHANGE_VQA
    assert decision.detected_input_type == InputType.BI_TEMPORAL
    assert decision.selected_model_id == "changestar"

def test_case_5_optical_sar_analysis():
    """CASE 5: Optical + SAR + 'Identify built-up regions using both images.' -> OPTICAL_SAR_ANALYSIS -> CROMA"""
    meta = [make_meta("sentinel2_opt.png", ModalityType.OPTICAL), make_meta("sentinel1_sar.png", ModalityType.SAR)]
    comp = CompatibilityResult(is_compatible=True, input_type=InputType.OPTICAL_SAR_PAIR, modality=ModalityType.OPTICAL_SAR)

    decision = RoutingEngine.route(
        query="Use the optical and SAR images together to identify built-up and water-covered regions.",
        images_metadata=meta,
        compatibility=comp
    )

    assert decision.is_executable is True
    assert decision.detected_task == TaskType.OPTICAL_SAR_ANALYSIS
    assert decision.detected_input_type == InputType.OPTICAL_SAR_PAIR
    assert decision.selected_model_id == "croma"

def test_case_6_single_image_with_change_query_rejection():
    """CASE 6: Single image + 'What changed?' -> Reject and explain two temporal images are required!"""
    meta = [make_meta("only_one_image.png", ModalityType.OPTICAL)]
    comp = CompatibilityResult(is_compatible=True, input_type=InputType.SINGLE_IMAGE, modality=ModalityType.OPTICAL)

    decision = RoutingEngine.route(
        query="What changed between these two dates?",
        images_metadata=meta,
        compatibility=comp
    )

    # MUST NOT route incorrectly!
    assert decision.is_executable is False
    assert decision.selected_model_id is None
    assert "Change analysis requires at least two temporal observations" in decision.blocking_issue
