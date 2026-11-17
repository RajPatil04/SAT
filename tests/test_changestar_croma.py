# tests/test_changestar_croma.py
import os
import sys
import time
import pytest
from pathlib import Path
import numpy as np

# Ensure SAT root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from model_services.test_data_generator import (
    generate_changestar_sample_pair,
    generate_croma_sample_pair
)


def test_environment_and_gpu():
    """Verify Python interpreter, PyTorch version, and NVIDIA CUDA accessibility."""
    import torch
    print(f"\n--- Environment Inspection ---")
    print(f"Python Version: {sys.version}")
    print(f"PyTorch Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU Device Count: {torch.cuda.device_count()}")
        print(f"GPU Device Name: {torch.cuda.get_device_name(0)}")
        props = torch.cuda.get_device_properties(0)
        print(f"Dedicated VRAM: {props.total_memory / (1024**3):.2f} GB")

    assert torch.__version__ is not None


def test_changestar_synthetic_data_generation():
    """Verify test data generator creates valid bi-temporal images."""
    t1, t2 = generate_changestar_sample_pair()
    assert t1.exists(), f"T1 image file does not exist: {t1}"
    assert t2.exists(), f"T2 image file does not exist: {t2}"
    from PIL import Image
    with Image.open(t1) as im1, Image.open(t2) as im2:
        assert im1.size == (512, 512)
        assert im2.size == (512, 512)
        assert im1.mode == "RGB"
        assert im2.mode == "RGB"


def test_croma_synthetic_data_generation():
    """Verify test data generator creates 2-channel SAR and 12-channel Optical arrays."""
    sar_path, opt_path = generate_croma_sample_pair()
    assert sar_path.exists(), f"SAR file does not exist: {sar_path}"
    assert opt_path.exists(), f"Optical file does not exist: {opt_path}"

    sar_arr = np.load(str(sar_path))
    opt_arr = np.load(str(opt_path))

    assert sar_arr.shape == (2, 120, 120), f"SAR shape must be (2, 120, 120), got {sar_arr.shape}"
    assert opt_arr.shape == (12, 120, 120), f"Optical shape must be (12, 120, 120), got {opt_arr.shape}"


def test_changestar_engine_inference():
    """Test ChangeStarEngine loading, 6-channel input preprocessing, and change prediction."""
    from model_services.changestar_engine import ChangeStarEngine
    engine = ChangeStarEngine.get_instance()
    assert engine.model is not None, "ChangeStar model failed to load"

    t1, t2 = generate_changestar_sample_pair()
    res = engine.predict(t1_input=t1, t2_input=t2, threshold=0.5)

    assert "change_percentage" in res
    assert "changed_pixels" in res
    assert "total_pixels" in res
    assert res["total_pixels"] > 0
    assert 0.0 <= res["change_percentage"] <= 100.0
    assert "change_mask_base64" in res
    assert res["change_mask_base64"].startswith("data:image/png;base64,")
    print(f"ChangeStar Test Passed: Changed Pixels={res['changed_pixels']}, Change %={res['change_percentage']}%, Latency={res['inference_time_ms']}ms")


def test_croma_engine_inference():
    """Test CROMAEngine loading, Sentinel-1 + Sentinel-2 preprocessing, and cross-attention representation."""
    from model_services.croma_engine import CROMAEngine
    engine = CROMAEngine.get_instance()
    assert engine.model is not None, "CROMA model failed to load"

    sar_path, opt_path = generate_croma_sample_pair()
    res = engine.predict(sar_input=sar_path, optical_input=opt_path, serialize_vectors=True)

    assert "feature_shapes" in res
    shapes = res["feature_shapes"]
    assert shapes["SAR_GAP"] == [1, 768]
    assert shapes["optical_GAP"] == [1, 768]
    assert shapes["joint_GAP"] == [1, 768]
    assert shapes["num_patches"] == 225
    assert shapes["embedding_dim"] == 768

    assert "metrics" in res
    sim = res["metrics"]["sar_optical_cosine_similarity"]
    assert -1.0 <= sim <= 1.0
    print(f"CROMA Test Passed: Joint Embedding Dim=768, Patches=225, Radar-Optical Sim={sim:.4f}, Latency={res['inference_time_ms']}ms")


def test_changestar_fastapi_endpoints():
    """Test ChangeStar FastAPI microservice endpoints using TestClient."""
    from fastapi.testclient import TestClient
    from model_services.changestar_server import app

    client = TestClient(app)
    # 1. Health check
    h_res = client.get("/health")
    assert h_res.status_code == 200
    h_data = h_res.json()
    assert h_data["status"] == "online"
    assert h_data["model_loaded"] is True

    # 2. Predict endpoint
    t1, t2 = generate_changestar_sample_pair()
    p_res = client.post("/predict", json={
        "t1_path": str(t1),
        "t2_path": str(t2),
        "threshold": 0.5
    })
    assert p_res.status_code == 200
    p_data = p_res.json()
    assert "answer" in p_data
    assert "confidence" in p_data
    assert "evidence" in p_data
    assert "change_percentage" in p_data["evidence"]
    assert "change_mask_url" in p_data["evidence"]


def test_croma_fastapi_endpoints():
    """Test CROMA FastAPI microservice endpoints using TestClient."""
    from fastapi.testclient import TestClient
    from model_services.croma_server import app

    client = TestClient(app)
    # 1. Health check
    h_res = client.get("/health")
    assert h_res.status_code == 200
    h_data = h_res.json()
    assert h_data["status"] == "online"
    assert h_data["model_loaded"] is True

    # 2. Predict endpoint
    sar_path, opt_path = generate_croma_sample_pair()
    p_res = client.post("/predict", json={
        "sar_path": str(sar_path),
        "optical_path": str(opt_path)
    })
    assert p_res.status_code == 200
    p_data = p_res.json()
    assert "answer" in p_data
    assert "evidence" in p_data
    assert "optical_feature_summary" in p_data["evidence"]
    assert "sar_feature_summary" in p_data["evidence"]


if __name__ == "__main__":
    test_environment_and_gpu()
    test_changestar_synthetic_data_generation()
    test_croma_synthetic_data_generation()
    test_changestar_engine_inference()
    test_croma_engine_inference()
    test_changestar_fastapi_endpoints()
    test_croma_fastapi_endpoints()
    print("\n>>> ALL TESTS COMPLETED SUCCESSFULLY! <<<")
