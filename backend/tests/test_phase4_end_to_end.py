# backend/tests/test_phase4_end_to_end.py
import pytest
import io
import os
import tempfile
from PIL import Image
from fastapi.testclient import TestClient
from backend.main import app
from backend.config.settings import settings

client = TestClient(app)

def create_sample_png_bytes(width=256, height=256, color=(100, 150, 200)) -> bytes:
    import numpy as np
    base = np.array(color, dtype=np.int16)
    noise = np.random.randint(-20, 21, size=(height, width, 3), dtype=np.int16)
    arr = np.clip(base + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_sample_sar_png_bytes(width=256, height=256) -> bytes:
    import numpy as np
    arr = np.random.randint(10, 80, size=(height, width), dtype=np.uint8)
    img = Image.fromarray(arr, mode="L")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_scenario_1_single_image_routed_to_geochat():
    """Test 1: Single-image request routed to GeoChat."""
    img_bytes = create_sample_png_bytes()
    response = client.post(
        "/api/analyze",
        files=[("images", ("aerial.png", img_bytes, "image/png"))],
        data={
            "question": "What objects and land-cover types are visible?",
            "input_mode": "SINGLE_IMAGE",
            "routing_config": "CONFIG_B"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("success", "unavailable")
    assert "GeoChat-7B" in data["models_used"] or data["routing"]["selected_model_id"] == "geochat-7b"
    assert data["task_type"] in ("SCENE_ANALYSIS", "OBJECT_ANALYSIS", "VQA")

def test_scenario_2_bitemporal_pair_routed_to_changestar():
    """Test 2: Bi-temporal pair routed to ChangeStar."""
    img1 = create_sample_png_bytes(color=(50, 100, 150))
    img2 = create_sample_png_bytes(color=(70, 120, 170))
    response = client.post(
        "/api/analyze",
        files=[
            ("images", ("t1.png", img1, "image/png")),
            ("images", ("t2.png", img2, "image/png"))
        ],
        data={
            "question": "What changes occurred between these two images?",
            "input_mode": "DOUBLE_IMAGE",
            "relationship": "BI_TEMPORAL",
            "routing_config": "CONFIG_B"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["routing"]["selected_model_id"] == "changestar"
    assert "ChangeStar" in data["models_used"] or data["routing"]["selected_model_name"] == "ChangeStar"

def test_scenario_3_optical_sar_routed_to_croma():
    """Test 3: Valid Optical-SAR input routed to CROMA."""
    opt_bytes = create_sample_png_bytes(color=(120, 180, 220))
    sar_bytes = create_sample_sar_png_bytes()
    response = client.post(
        "/api/analyze",
        files=[
            ("images", ("sentinel2_optical.png", opt_bytes, "image/png")),
            ("images", ("sentinel1_sar.png", sar_bytes, "image/png"))
        ],
        data={
            "question": "Compare the structural information visible in these images.",
            "input_mode": "DOUBLE_IMAGE",
            "relationship": "OPTICAL_SAR",
            "routing_config": "CONFIG_B"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["routing"]["selected_model_id"] == "croma"
    assert "CROMA" in data["models_used"] or data["routing"]["selected_model_name"] == "CROMA"

def test_scenario_4_invalid_file_handling():
    """Test 4: Invalid file format rejection."""
    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00"
    response = client.post(
        "/api/analyze",
        files=[("images", ("payload.exe", fake_exe, "application/octet-stream"))],
        data={
            "question": "Describe this",
            "input_mode": "SINGLE_IMAGE"
        }
    )
    assert response.status_code == 400
    assert "unsupported" in response.text.lower() or "errors" in response.json().get("detail", {})

def test_scenario_5_ambiguous_question_handling():
    """Test 5: Ambiguous question handling with transparent assumption."""
    img_bytes = create_sample_png_bytes()
    response = client.post(
        "/api/analyze",
        files=[("images", ("scene.png", img_bytes, "image/png"))],
        data={
            "question": "?",
            "input_mode": "SINGLE_IMAGE",
            "routing_config": "CONFIG_B"
        }
    )
    assert response.status_code == 200
    data = response.json()
    reasons_str = " ".join(data["routing"]["reasons"])
    assert "Ambiguity noted" in reasons_str or "ambiguous" in reasons_str.lower()

def test_scenario_6_missing_model_service_handling(monkeypatch):
    """Test 6: Missing model service handling without fabrication."""
    # Temporarily set mock fallback to False
    monkeypatch.setattr(settings, "ENABLE_MOCK_FALLBACK_FOR_TESTS", False)
    monkeypatch.setattr(settings, "GEOCHAT_API_URL", "http://127.0.0.1:9999/nonexistent")

    img_bytes = create_sample_png_bytes()
    response = client.post(
        "/api/analyze",
        files=[("images", ("single.png", img_bytes, "image/png"))],
        data={
            "question": "What objects and land-cover types are visible?",
            "input_mode": "SINGLE_IMAGE",
            "routing_config": "CONFIG_B"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("unavailable", "error")
    assert "failed" in data["answer"].lower() or "unavailable" in data["answer"].lower() or "error" in data["answer"].lower()

def test_scenario_7_model_inference_failure_handling(monkeypatch):
    """Test 7: Model inference failure handled gracefully with structured response."""
    from backend.models.geochat_adapter import GeoChatAdapter

    async def broken_predict(*args, **kwargs):
        raise RuntimeError("Simulated GPU Out-Of-Memory Error during forward pass")

    monkeypatch.setattr(GeoChatAdapter, "predict", broken_predict)

    img_bytes = create_sample_png_bytes()
    response = client.post(
        "/api/analyze",
        files=[("images", ("test.png", img_bytes, "image/png"))],
        data={
            "question": "Describe the important features in this image.",
            "input_mode": "SINGLE_IMAGE",
            "routing_config": "CONFIG_B"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("unavailable", "error")
    assert "Model execution failed" in data["answer"] or "GPU Out-Of-Memory" in data["answer"]

def test_scenario_8_cross_model_reasoning_disabled_config_b():
    """Test 8: Cross-model reasoning disabled under Configuration B."""
    img1 = create_sample_png_bytes(color=(10, 20, 30))
    img2 = create_sample_png_bytes(color=(40, 50, 60))
    response = client.post(
        "/api/analyze",
        files=[
            ("images", ("t1.png", img1, "image/png")),
            ("images", ("t2.png", img2, "image/png"))
        ],
        data={
            "question": "What changes occurred between these two images?",
            "input_mode": "DOUBLE_IMAGE",
            "relationship": "BI_TEMPORAL",
            "routing_config": "CONFIG_B"  # Disabled cross-model reasoning
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["routing_config"] == "CONFIG_B"
    # Under Config B, only ChangeStar is invoked
    assert len(data["selected_models"]) == 1
    assert "ChangeStar" in data["selected_models"][0]
    assert data["timings"]["cross_reasoning_ms"] == 0.0

def test_scenario_9_cross_model_reasoning_enabled_config_c():
    """Test 9: Cross-model reasoning enabled under Configuration C for descriptive change questions."""
    img1 = create_sample_png_bytes(color=(15, 25, 35))
    img2 = create_sample_png_bytes(color=(45, 55, 65))
    response = client.post(
        "/api/analyze",
        files=[
            ("images", ("t1.png", img1, "image/png")),
            ("images", ("t2.png", img2, "image/png"))
        ],
        data={
            "question": "What changes occurred between these two images?",
            "input_mode": "DOUBLE_IMAGE",
            "relationship": "BI_TEMPORAL",
            "routing_config": "CONFIG_C"  # Enabled cross-model reasoning
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["routing_config"] == "CONFIG_C"
    # Under Config C, both ChangeStar and GeoChat-7B are invoked
    assert len(data["selected_models"]) == 2
    assert any("ChangeStar" in m for m in data["selected_models"])
    assert any("GeoChat" in m for m in data["selected_models"])
    assert data["timings"]["cross_reasoning_ms"] >= 0.0

def test_scenario_10_api_endpoints_health_models_validate():
    """Test 10: API endpoints GET /health, GET /models/status, POST /validate."""
    # GET /health
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "online"

    # GET /models/status
    res_status = client.get("/models/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert "geochat-7b" in status_data
    assert "changestar" in status_data
    assert "croma" in status_data

    # POST /validate
    img_bytes = create_sample_png_bytes()
    res_val = client.post(
        "/validate",
        files=[("images", ("sample.png", img_bytes, "image/png"))],
        data={
            "input_mode": "SINGLE_IMAGE",
            "question": "Identify visible roads and buildings."
        }
    )
    assert res_val.status_code == 200
    val_data = res_val.json()
    assert val_data["is_valid"] is True
    assert len(val_data["images"]) == 1
    assert val_data["images"][0]["width"] == 256
