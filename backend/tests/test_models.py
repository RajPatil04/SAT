# backend/tests/test_models.py
import pytest
import asyncio
from backend.router.model_registry import ModelRegistry
from backend.models import get_adapter
from backend.models.mock_adapter import MockSpecialistAdapter

def test_model_registry_registered_models():
    models = ModelRegistry.list_models()
    model_ids = {m.model_id for m in models}
    assert "geochat-7b" in model_ids
    assert "changestar" in model_ids
    assert "croma" in model_ids
    assert "grounding-specialist" in model_ids

def test_mock_specialist_adapter_predict():
    adapter = MockSpecialistAdapter("test-model", "Test Specialist", "VLM")
    res = asyncio.run(adapter.predict(
        query="Describe the land cover",
        file_paths=[],
        task="CAPTIONING"
    ))

    assert res["is_simulated"] is True
    assert res["confidence"] is None  # Scientifically honest: no fabricated confidence!
    assert "Test Specialist" in res["answer"]
    assert "evidence" in res
    assert res["model_latency_ms"] >= 0.0

def test_get_adapter_instances():
    geo_adapter = get_adapter("geochat-7b")
    assert geo_adapter.model_id == "geochat-7b"

    change_adapter = get_adapter("changestar")
    assert change_adapter.model_id == "changestar"

    croma_adapter = get_adapter("croma")
    assert croma_adapter.model_id == "croma"
