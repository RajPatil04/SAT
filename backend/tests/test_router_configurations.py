# backend/tests/test_router_configurations.py
import pytest
from backend.router.router import SatQueryRouter, RoutingConfiguration, TaskCategory
from backend.router.schemas import ImageMetadata, ModalityType, TaskType
from backend.services.input_validator import InputValidator

def make_metadata(filename: str, width: int = 512, height: int = 512, channels: int = 3, modality: ModalityType = ModalityType.OPTICAL) -> ImageMetadata:
    return ImageMetadata(
        filename=filename,
        format="PNG",
        width=width,
        height=height,
        channels=channels,
        datatype=f"RGB ({channels} bands)",
        is_geotiff=False,
        detected_modality=modality,
        file_size_bytes=102400
    )

def test_config_a_fixed_routing_single_image():
    """Config A routes Single Image mode directly to GeoChat-7B regardless of query."""
    meta = [make_metadata("aerial.png")]
    decision = SatQueryRouter.route_request(
        input_mode="SINGLE_IMAGE",
        question="What objects are in this image?",
        relationship=None,
        metadata_list=meta,
        validation_result=None,
        compatibility_result=None,
        routing_config=RoutingConfiguration.CONFIG_A
    )
    assert decision["is_executable"] is True
    assert decision["selected_model_id"] == "geochat-7b"
    assert decision["invoke_secondary_model"] is False

def test_config_a_fixed_routing_double_image_bitemporal():
    """Config A routes Double Image with bi-temporal relationship directly to ChangeStar."""
    meta = [make_metadata("t1.png"), make_metadata("t2.png")]
    decision = SatQueryRouter.route_request(
        input_mode="DOUBLE_IMAGE",
        question="Describe this pair",
        relationship="BI_TEMPORAL",
        metadata_list=meta,
        validation_result=None,
        compatibility_result=None,
        routing_config=RoutingConfiguration.CONFIG_A
    )
    assert decision["is_executable"] is True
    assert decision["selected_model_id"] == "changestar"
    assert decision["invoke_secondary_model"] is False

def test_config_a_fixed_routing_double_image_optical_sar():
    """Config A routes Double Image with optical-sar relationship directly to CROMA."""
    meta = [make_metadata("opt.png"), make_metadata("sar.png", channels=2, modality=ModalityType.SAR)]
    decision = SatQueryRouter.route_request(
        input_mode="DOUBLE_IMAGE",
        question="Compare features",
        relationship="OPTICAL_SAR",
        metadata_list=meta,
        validation_result=None,
        compatibility_result=None,
        routing_config=RoutingConfiguration.CONFIG_A
    )
    assert decision["is_executable"] is True
    assert decision["selected_model_id"] == "croma"
    assert decision["invoke_secondary_model"] is False

def test_config_a_fixed_routing_double_image_unknown_fails():
    """Config A cannot route when relationship is Unknown in Double Image mode."""
    meta = [make_metadata("img1.png"), make_metadata("img2.png")]
    decision = SatQueryRouter.route_request(
        input_mode="DOUBLE_IMAGE",
        question="Compare features",
        relationship="UNKNOWN",
        metadata_list=meta,
        validation_result=None,
        compatibility_result=None,
        routing_config=RoutingConfiguration.CONFIG_A
    )
    assert decision["is_executable"] is False
    assert "cannot determine a specialist model when relationship is Unknown" in decision["blocking_issue"]

def test_config_b_query_driven_single_image_with_change_query_rejected():
    """Config B rejects change detection query when only single image is provided."""
    meta = [make_metadata("single.png")]
    decision = SatQueryRouter.route_request(
        input_mode="SINGLE_IMAGE",
        question="What changed between these two images?",
        relationship=None,
        metadata_list=meta,
        validation_result=None,
        compatibility_result=None,
        routing_config=RoutingConfiguration.CONFIG_B
    )
    assert decision["is_executable"] is False
    assert "requires at least two temporal observations" in decision["blocking_issue"]

def test_config_b_query_driven_double_image_single_focus_routes_to_geochat():
    """Config B dynamically routes to GeoChat when user only asks about the first image in a pair."""
    meta = [make_metadata("t1.png"), make_metadata("t2.png")]
    decision = SatQueryRouter.route_request(
        input_mode="DOUBLE_IMAGE",
        question="Describe the land cover in the first image",
        relationship="BI_TEMPORAL",
        metadata_list=meta,
        validation_result=None,
        compatibility_result=None,
        routing_config=RoutingConfiguration.CONFIG_B
    )
    assert decision["is_executable"] is True
    assert decision["selected_model_id"] == "geochat-7b"
    assert decision["invoke_secondary_model"] is False

def test_config_c_cross_model_reasoning_triggered_on_explanatory_change_query():
    """Config C selectively triggers secondary reasoning (ChangeStar + GeoChat) for descriptive change questions."""
    meta = [make_metadata("t1.png"), make_metadata("t2.png")]
    decision = SatQueryRouter.route_request(
        input_mode="DOUBLE_IMAGE",
        question="What changes occurred between these two images?",
        relationship="BI_TEMPORAL",
        metadata_list=meta,
        validation_result=None,
        compatibility_result=None,
        routing_config=RoutingConfiguration.CONFIG_C
    )
    assert decision["is_executable"] is True
    assert decision["selected_model_id"] == "changestar"
    assert decision["invoke_secondary_model"] is True
    assert decision["secondary_model_id"] == "geochat-7b"
    assert "Cross-Model Reasoning Justified" in decision["secondary_justification"]

def test_config_c_cross_model_not_triggered_for_single_image():
    """Config C does NOT trigger unnecessary secondary models for standard single-image queries."""
    meta = [make_metadata("optical.png")]
    decision = SatQueryRouter.route_request(
        input_mode="SINGLE_IMAGE",
        question="What objects and land-cover types are visible?",
        relationship=None,
        metadata_list=meta,
        validation_result=None,
        compatibility_result=None,
        routing_config=RoutingConfiguration.CONFIG_C
    )
    assert decision["is_executable"] is True
    assert decision["selected_model_id"] == "geochat-7b"
    assert decision["invoke_secondary_model"] is False

def test_ambiguous_query_handling():
    """Router detects ambiguous queries and provides transparent assumption."""
    meta = [make_metadata("optical.png")]
    decision = SatQueryRouter.route_request(
        input_mode="SINGLE_IMAGE",
        question="?",
        relationship=None,
        metadata_list=meta,
        validation_result=None,
        compatibility_result=None,
        routing_config=RoutingConfiguration.CONFIG_B
    )
    assert decision["is_executable"] is True
    assert decision["selected_model_id"] == "geochat-7b"
    assert "Ambiguity noted" in " ".join(decision["reasons"])
