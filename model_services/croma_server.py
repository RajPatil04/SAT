# model_services/croma_server.py
import os
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure SAT root and model_services in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from model_services.croma_engine import CROMAEngine

app = FastAPI(
    title="CROMA Foundation Model Service",
    description="Dedicated microservice serving official CROMA Base (SAR + Optical Foundation Model) for multimodal remote sensing representation extraction.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine: Optional[CROMAEngine] = None

@app.on_event("startup")
def startup_event():
    global engine
    try:
        engine = CROMAEngine.get_instance()
    except Exception as e:
        print(f"Warning: CROMA model engine startup error: {e}")

class CROMARequest(BaseModel):
    optical_path: str = Field(..., description="Local filepath to Sentinel-2 Optical imagery (.npy, .npz, or image)")
    sar_path: str = Field(..., description="Local filepath to Sentinel-1 SAR imagery (.npy, .npz, or image)")
    query: Optional[str] = Field(None, description="Optional task query")
    task: Optional[str] = Field("cross_modal_representation", description="Task identifier")
    serialize_vectors: Optional[bool] = Field(False, description="Whether to include full 768-d feature arrays in response")

class GradioCompatRequest(BaseModel):
    data: List[Any] = Field(..., description="Gradio payload [optical_path, sar_path, query]")

@app.get("/health")
def health():
    import torch
    global engine
    if engine is None:
        try:
            engine = CROMAEngine.get_instance()
        except Exception:
            pass
    is_loaded = engine is not None and engine.model is not None
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A"
    return {
        "status": "online" if is_loaded else "initializing",
        "service": "CROMA Multimodal Foundation Service",
        "model_loaded": is_loaded,
        "model_name": "CROMA Base (Modality: both)",
        "device": str(engine.device) if engine else "uninitialized",
        "cuda_available": torch.cuda.is_available(),
        "gpu_device": gpu_name,
        "input_conventions": {
            "sar_channels": 2,
            "optical_channels": 12,
            "resolution": "120x120 pixels"
        }
    }

@app.get("/model_info")
def model_info():
    return {
        "model_name": "CROMA (Contrastive Radar-Optical Masked Autoencoders)",
        "architecture": "Vision Transformer + Cross Attention Fusion",
        "modalities": "Sentinel-1 SAR (2 ch) + Sentinel-2 Optical (12 ch)",
        "patch_size": 8,
        "num_patches": 225,
        "embedding_dim": 768,
        "supported_input_formats": [".npy", ".npz", ".pt", "multiband image"],
        "paper": "NeurIPS 2023 (https://arxiv.org/abs/2311.00566)",
        "huggingface": "https://huggingface.co/antofuller/CROMA"
    }

@app.post("/predict")
def predict(req: CROMARequest):
    global engine
    if not engine:
        try:
            engine = CROMAEngine.get_instance()
        except Exception:
            raise HTTPException(status_code=503, detail="CROMA Engine is not initialized")

    sar_p = Path(req.sar_path)
    opt_p = Path(req.optical_path)
    if not sar_p.exists():
        raise HTTPException(status_code=400, detail=f"SAR path does not exist: {req.sar_path}")
    if not opt_p.exists():
        raise HTTPException(status_code=400, detail=f"Optical path does not exist: {req.optical_path}")

    try:
        result = engine.predict(
            sar_input=sar_p,
            optical_input=opt_p,
            serialize_vectors=req.serialize_vectors or False
        )

        # Structure response to be 100% compatible with SatQuery AI CROMAAdapter
        sim = result["metrics"]["sar_optical_cosine_similarity"]
        answer_text = (
            f"CROMA processed paired SAR (2 ch) and Optical (12 ch) scenes. "
            f"Extracted 768-dim joint representations across 225 patches. "
            f"Cross-modal radar-optical alignment cosine similarity: {sim:.4f}."
        )

        return {
            "answer": answer_text,
            "confidence": None,  # Contrastive feature extraction does not yield calibrated posterior probability
            "evidence": {
                "text": f"Radar and optical cross-attention fusion produced joint embeddings with similarity index {sim:.4f}.",
                "cross_modal_similarity": sim,
                "optical_feature_summary": {
                    "num_patches": result["feature_shapes"]["num_patches"],
                    "embedding_dim": result["feature_shapes"]["embedding_dim"],
                    "optical_norm": result["metrics"]["optical_gap_l2_norm"]
                },
                "sar_feature_summary": {
                    "sar_norm": result["metrics"]["sar_gap_l2_norm"],
                    "joint_norm": result["metrics"]["joint_gap_l2_norm"]
                }
            },
            "model_latency_ms": result["inference_time_ms"],
            "raw_output": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CROMA inference error: {str(e)}")

@app.post("/api/predict")
def gradio_predict_compat(req: GradioCompatRequest):
    """Gradio-compatible endpoint for SatQuery AI when configured with api_type=gradio."""
    if len(req.data) < 2:
        raise HTTPException(status_code=400, detail="Expected [optical_path, sar_path, (optional query)] in data array")
    opt_path = str(req.data[0])
    sar_path = str(req.data[1])
    query = str(req.data[2]) if len(req.data) > 2 else ""

    res = predict(CROMARequest(optical_path=opt_path, sar_path=sar_path, query=query))
    return {
        "data": [res["answer"]],
        "answer": res["answer"],
        "confidence": res["confidence"],
        "evidence": res["evidence"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("model_services.croma_server:app", host="127.0.0.1", port=8002, reload=False)
