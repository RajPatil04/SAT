# backend/tests/test_model_inference_logic.py
import pytest
import os
import asyncio
import numpy as np
from pathlib import Path
from PIL import Image

from backend.config.settings import settings
from backend.models.geochat_adapter import GeoChatAdapter
from backend.models.changestar_adapter import ChangeStarAdapter
from backend.models.mock_adapter import MockSpecialistAdapter
from backend.services.cross_model_reasoner import SelectiveCrossModelReasoner
from backend.services.input_validator import InputValidator
from backend.router.schemas import ModalityType

def test_mock_responses_cannot_appear_as_genuine_inference(monkeypatch):
    """
    Requirement 1: With mock fallback disabled (production/live research mode),
    calling an unconfigured model adapter MUST raise RuntimeError and NEVER
    return a synthetic mock string such as '[MOCK SPECIALIST: ...]'.
    """
    monkeypatch.setattr(settings, "ENABLE_MOCK_FALLBACK_FOR_TESTS", False)
    monkeypatch.setattr(settings, "GEOCHAT_API_URL", None)

    adapter = GeoChatAdapter()
    assert not adapter.is_configured()

    async def run():
        with pytest.raises(RuntimeError) as exc_info:
            await adapter.predict(
                query="Describe this scene",
                file_paths=["dummy_path.png"],
                task="VQA"
            )
        assert "GeoChat-7B" in str(exc_info.value)
        assert "not configured" in str(exc_info.value).lower() or "unavailable" in str(exc_info.value).lower()

    asyncio.run(run())

def test_missing_geochat_service_does_not_generate_fake_answer_or_appear_in_models_used(monkeypatch):
    """
    Requirement 3 & 4: In cross-model reasoning (e.g. ChangeStar + GeoChat),
    if GeoChat is unconfigured, the system must:
    1. NOT invoke GeoChat
    2. NOT include GeoChat in models_used (only ChangeStar)
    3. NOT fabricate vegetation/infrastructure descriptions
    4. Return the honest primary ChangeStar result
    """
    monkeypatch.setattr(settings, "ENABLE_MOCK_FALLBACK_FOR_TESTS", False)
    monkeypatch.setattr(settings, "GEOCHAT_API_URL", None)

    primary_output = {
        "answer": "ChangeStar detected 0.3376% changed surface area between temporal observations.",
        "confidence": 0.94,
        "evidence": {
            "change_percentage": 0.3376,
            "changed_pixels": 885,
            "total_pixels": 262144,
            "change_mask_url": "/api/uploads/change_mask_123.png"
        },
        "model_latency_ms": 42.0
    }

    routing_info = {
        "selected_model_name": "ChangeStar",
        "invoke_secondary_model": True,
        "secondary_model_id": "geochat-7b",
        "secondary_model_role": "VLM Specialist",
        "secondary_justification": "Synthesize semantic description",
        "reasons": ["Bi-temporal change detected"]
    }

    async def run():
        result = await SelectiveCrossModelReasoner.reason(
            query="What changes occurred between these two images?",
            file_paths=["uploads/sample_data/sample_t1_levir.png", "uploads/sample_data/sample_t2_levir.png"],
            primary_output=primary_output,
            routing_info=routing_info
        )

        # 1. GeoChat-7B must NOT be in models_used
        assert result["models_used"] == ["ChangeStar"]
        assert "GeoChat-7B" not in result["models_used"]

        # 2. No mock specialist strings or invented descriptions
        assert "MOCK SPECIALIST" not in result["answer"]
        assert "expansion in built-up infrastructure" not in result["answer"]
        assert result["answer"] == primary_output["answer"]

        # 3. Invocations trace records GeoChat as skipped/unconfigured
        invocations = result["invocations"]
        assert len(invocations) == 2
        sec_inv = invocations[1]
        assert sec_inv["model_name"] == "GeoChat-7B"
        assert sec_inv["used_in_final_answer"] is False
        assert "unconfigured" in sec_inv["errors"].lower()

    asyncio.run(run())

def test_changestar_inference_errors_do_not_become_zero_percent_results(monkeypatch):
    """
    Requirement 2: If ChangeStar inference fails (e.g. missing files or model fault),
    it must raise an exception rather than returning a false 0.0% success.
    """
    monkeypatch.setattr(settings, "ENABLE_MOCK_FALLBACK_FOR_TESTS", False)
    adapter = ChangeStarAdapter()

    async def run():
        # Pass nonexistent files
        with pytest.raises(FileNotFoundError):
            await adapter.predict(
                query="Detect changes",
                file_paths=["nonexistent_t1.png", "nonexistent_t2.png"],
                task="CHANGE_DETECTION"
            )

    asyncio.run(run())

def test_changestar_calculates_real_changed_pixel_percentage():
    """
    Requirement 2: ChangeStar inference on actual LEVIR-CD temporal observations
    must calculate genuine changed pixels and percentages from model probabilities,
    not a hardcoded 0.0%.
    """
    from model_services.changestar_engine import ChangeStarEngine
    t1_path = Path("uploads/sample_data/sample_t1_levir.png")
    t2_path = Path("uploads/sample_data/sample_t2_levir.png")

    if not t1_path.exists() or not t2_path.exists():
        pytest.skip("Sample LEVIR images not found in uploads/sample_data")

    engine = ChangeStarEngine.get_instance()
    result = engine.predict(t1_input=t1_path, t2_input=t2_path, threshold=0.5)

    assert result["total_pixels"] == 262144
    assert result["changed_pixels"] > 0
    assert result["change_percentage"] > 0.0
    assert "change_mask_base64" in result
    assert result["max_change_probability"] > 0.5

def test_solid_color_and_blank_images_are_rejected_with_validation_error(tmp_path):
    """
    Requirement 5: Inspect decoded contents and reject solid-color / blank images
    with near-zero pixel variance (std < 0.5) with a clear validation error.
    """
    # Create a 100x100 uniform solid-color image (std = 0.0)
    solid_img_path = str(tmp_path / "solid_blank.png")
    img = Image.new("RGB", (100, 100), color=(128, 128, 128))
    img.save(solid_img_path)

    res = InputValidator.validate_saved_files(
        file_paths=[solid_img_path],
        question="Analyze this satellite scene",
        input_mode="SINGLE_IMAGE"
    )

    assert res.is_valid is False
    assert len(res.blocking_errors) > 0
    err_text = " ".join(res.blocking_errors).lower()
    assert "uniform solid color" in err_text or "blank" in err_text
    assert res.images[0].is_valid is False
    assert res.images[0].variance == 0.0

def test_explicit_mock_testing_mode_is_visibly_identified():
    """
    Requirement 7: Explicit MockSpecialistAdapter is strictly marked as simulated
    (is_simulated = True) and clearly labels its outputs as simulated.
    """
    mock = MockSpecialistAdapter("test-model", "TestModel", "Specialist Role")
    assert mock.is_configured() is True
    
    async def run():
        res = await mock.predict(query="test", file_paths=[], task="VQA")
        assert res["is_simulated"] is True
        assert "[MOCK SPECIALIST: TestModel]" in res["answer"]
    
    asyncio.run(run())

def test_geochat_url_changes_when_configuration_file_updated(tmp_path):
    """
    Section 3: Changing the GeoChat URL in model_endpoints.yaml changes the endpoint used,
    without editing React components, routing logic, or model adapters.
    """
    from backend.config.endpoint_config import EndpointsConfiguration
    custom_yaml = tmp_path / "model_endpoints.yaml"
    custom_yaml.write_text("""
services:
  geochat:
    base_url: "https://custom-geochat-service.internal"
    api_type: "gradio"
    enabled: true
  changestar:
    base_url: "http://127.0.0.1:8001"
    enabled: true
""", encoding="utf-8")

    cfg = EndpointsConfiguration.load_from_file(custom_yaml)
    geochat_cfg = cfg.get_service("geochat")
    assert geochat_cfg.base_url == "https://custom-geochat-service.internal"
    assert geochat_cfg.is_configured() is True
    assert geochat_cfg.api_type == "gradio"

def test_no_hardcoded_geochat_service_urls_in_source_code():
    """
    Section 3: Verifies no hardcoded GeoChat URLs exist in frontend or python source code.
    Only model_endpoints.yaml is authoritative for service endpoints.
    """
    sat_root = Path(__file__).resolve().parent.parent.parent
    found_hardcoded = []
    
    import re
    # Match actual http:// or https:// URLs that point to geochat instances, excluding placeholders in comments/docstrings
    url_pattern = re.compile(r"https?://[a-zA-Z0-9_\-\.:]+", re.IGNORECASE)

    for ext in ("*.py", "*.ts", "*.tsx"):
        for p in sat_root.glob(f"**/{ext}"):
            # Skip virtualenvs or cache
            if ".venv" in str(p) or "node_modules" in str(p) or ".git" in str(p) or "endpoint_config.py" in str(p):
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                for line in content.splitlines():
                    if ("http://" in line or "https://" in line) and "geochat" in line.lower() and not line.strip().startswith("#"):
                        # If it's a test assertion or comment, allow
                        if "assert" not in line and "test" not in str(p):
                            # Ignore docstrings/placeholders
                            if "REPLACE-WITH" not in line:
                                found_hardcoded.append((p.name, line.strip()))
            except Exception:
                pass

    assert len(found_hardcoded) == 0, f"Found hardcoded GeoChat URLs: {found_hardcoded}"

def test_optical_sar_rejects_plain_rgb_pair(tmp_path):
    """
    Section 6: Ordinary RGB images without radar backscatter channels must not be
    treated as a valid Optical-SAR pair. CROMA requires genuine radar + optical inputs.
    """
    img1 = str(tmp_path / "opt1.png")
    img2 = str(tmp_path / "opt2.png")
    # Both are 3-channel RGB with variance
    arr1 = np.random.randint(50, 200, size=(100, 100, 3), dtype=np.uint8)
    arr2 = np.random.randint(50, 200, size=(100, 100, 3), dtype=np.uint8)
    Image.fromarray(arr1, mode="RGB").save(img1)
    Image.fromarray(arr2, mode="RGB").save(img2)

    res = InputValidator.validate_saved_files(
        file_paths=[img1, img2],
        question="Analyze multimodal features",
        input_mode="DOUBLE_IMAGE",
        relationship="OPTICAL_SAR"
    )

    assert res.modality_compatible is False
    assert any("Optical-SAR Modality Alert" in w for w in res.warnings)

def test_empty_evidence_does_not_produce_fabricated_change_map():
    """
    Section 10: If a model produces no change map or overlay, the system
    must never fabricate or manufacture a fake one.
    """
    from backend.services.evidence_service import EvidenceService
    evidence = EvidenceService.normalize_evidence(
        raw_evidence={"text": "Scene description completed."},
        task="VQA",
        supports_grounding=False,
        supports_change_maps=False
    )
    assert evidence.change_mask_url is None
    assert evidence.overlay_url is None

