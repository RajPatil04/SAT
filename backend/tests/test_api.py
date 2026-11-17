# backend/tests/test_api.py
import pytest
import io
from PIL import Image
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def create_test_image_bytes():
    import numpy as np
    arr = np.random.randint(50, 200, size=(256, 256, 3), dtype=np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"

def test_api_system_status():
    res = client.get("/api/system-status")
    assert res.status_code == 200
    data = res.json()
    assert "fastapi" in data
    assert "models" in data

def test_api_models():
    res = client.get("/api/models")
    assert res.status_code == 200
    models = res.json()
    assert len(models) >= 3

def test_api_capabilities():
    res = client.get("/api/models/capabilities")
    assert res.status_code == 200
    caps = res.json()
    assert "supported_tasks" in caps
    assert "routing_formulation" in caps

def test_api_analyze_single():
    img_bytes = create_test_image_bytes()
    files = [("images", ("test_sat.png", img_bytes, "image/png"))]
    data = {"question": "Describe the land cover in this scene."}

    res = client.post("/api/analyze", files=files, data=data)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] in ("success", "unavailable")
    assert "GeoChat" in body.get("answer", "") or "geochat-7b" in str(body.get("routing", {}).get("selected_model_id"))
    assert len(body["execution_trace"]) >= 5

def test_api_benchmark_evaluation():
    res = client.post("/api/experiments/evaluate-benchmark")
    assert res.status_code == 200
    data = res.json()
    assert "task_classification_accuracy" in data
    assert "routing_accuracy" in data
    assert data["total_benchmark_cases"] >= 6
