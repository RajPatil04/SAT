# model_services/changestar_server.py
import os
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

# Ensure SAT root and model_services in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from model_services.changestar_engine import ChangeStarEngine

app = FastAPI(
    title="ChangeStar Change Detection Service",
    description="Dedicated microservice serving official ChangeStar (ResNet-18, LEVIR-CD) for bi-temporal remote sensing change detection.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine: Optional[ChangeStarEngine] = None

@app.on_event("startup")
def startup_event():
    global engine
    try:
        engine = ChangeStarEngine.get_instance()
    except Exception as e:
        # Log error but allow server to start for health debugging
        print(f"Warning: ChangeStar model engine startup error: {e}")

class ChangeStarRequest(BaseModel):
    t1_path: str = Field(..., description="Local filepath to pre-change (T1) optical image")
    t2_path: str = Field(..., description="Local filepath to post-change (T2) optical image")
    threshold: Optional[float] = Field(0.5, description="Decision threshold for change probability (0.0 - 1.0)")
    query: Optional[str] = Field(None, description="Optional user query / task prompt")
    task: Optional[str] = Field("change_detection", description="Task identifier")
    target_size: Optional[List[int]] = Field(None, description="Optional [width, height] spatial resize")

class GradioCompatRequest(BaseModel):
    data: List[Any] = Field(..., description="Gradio payload [t1_path, t2_path, query]")

@app.get("/health")
def health():
    import torch
    global engine
    if engine is None:
        try:
            engine = ChangeStarEngine.get_instance()
        except Exception:
            pass
    is_loaded = engine is not None and engine.model is not None
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A"
    return {
        "status": "online" if is_loaded else "initializing",
        "service": "ChangeStar Remote-Sensing Service",
        "model_loaded": is_loaded,
        "model_name": "ChangeStar-1x96 (ResNet-18, LEVIR-CD)",
        "device": str(engine.device) if engine else "uninitialized",
        "cuda_available": torch.cuda.is_available(),
        "gpu_device": gpu_name,
        "input_convention": "Bi-temporal 6-channel concatenation [B, 6, H, W]"
    }

@app.get("/model_info")
def model_info():
    return {
        "model_name": "ChangeStar-1x96",
        "backbone": "ResNet-18",
        "dataset": "LEVIR-CD",
        "input_shape": "[B, 6, H, W]",
        "output_shape": "[B, 1, H, W]",
        "f1_score": 90.5,
        "supported_formats": ["PNG", "JPEG", "TIFF"],
        "recommended_resolution": "512x512",
        "repo": "https://github.com/Z-Zheng/Changen"
    }

@app.post("/predict")
def predict(req: ChangeStarRequest):
    global engine
    if not engine:
        try:
            engine = ChangeStarEngine.get_instance()
        except Exception:
            raise HTTPException(status_code=503, detail="ChangeStar Engine is not initialized")

    t1 = Path(req.t1_path)
    t2 = Path(req.t2_path)
    if not t1.exists():
        raise HTTPException(status_code=400, detail=f"T1 image path does not exist: {req.t1_path}")
    if not t2.exists():
        raise HTTPException(status_code=400, detail=f"T2 image path does not exist: {req.t2_path}")

    target_size = tuple(req.target_size) if req.target_size and len(req.target_size) == 2 else None

    try:
        result = engine.predict(
            t1_input=t1,
            t2_input=t2,
            threshold=req.threshold or 0.5,
            target_size=target_size
        )

        # Structure response to be 100% compatible with SatQuery AI ChangeModelAdapter
        change_pct = result["change_percentage"]
        if result["changed_pixels"] == 0:
            answer_text = (
                f"ChangeStar detected 0.0% changed surface area (0 changed pixels out of {result['total_pixels']} total pixels). "
                f"No significant structural changes were detected between the two observation epochs at decision threshold {req.threshold or 0.5}."
            )
        else:
            answer_text = (
                f"ChangeStar detected {change_pct}% changed surface area between temporal observations. "
                f"Evaluated {result['changed_pixels']} changed pixels out of {result['total_pixels']} total pixels."
            )

        # Save change mask file into uploads for persistent URL retrieval
        uploads_dir = BASE_DIR / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        mask_filename = f"change_mask_{int(time.time() * 1000)}.png"
        mask_path = uploads_dir / mask_filename

        import base64
        mask_bytes = base64.b64decode(result["change_mask_base64"].split(",")[1])
        with open(mask_path, "wb") as f:
            f.write(mask_bytes)

        return {
            "answer": answer_text,
            "confidence": None,  # Change detection mask does not yield calibrated posterior probability
            "evidence": {
                "text": f"LEVIR-CD change detector verified spatial transitions over {change_pct}% of the surveyed extent.",
                "change_percentage": change_pct,
                "change_mask_url": f"/api/uploads/{mask_filename}",
                "changed_pixels": result["changed_pixels"],
                "total_pixels": result["total_pixels"]
            },
            "model_latency_ms": result["inference_time_ms"],
            "raw_output": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@app.post("/api/predict")
def gradio_predict_compat(req: GradioCompatRequest):
    """Gradio-compatible endpoint for SatQuery AI when configured with api_type=gradio."""
    if len(req.data) < 2:
        raise HTTPException(status_code=400, detail="Expected [t1_path, t2_path, (optional query)] in data array")
    t1_path = str(req.data[0])
    t2_path = str(req.data[1])
    query = str(req.data[2]) if len(req.data) > 2 else ""

    res = predict(ChangeStarRequest(t1_path=t1_path, t2_path=t2_path, query=query))
    return {
        "data": [res["answer"]],
        "answer": res["answer"],
        "confidence": res["confidence"],
        "evidence": res["evidence"]
    }

@app.post("/predict_upload")
async def predict_upload(
    file_t1: UploadFile = File(..., description="Pre-change T1 image"),
    file_t2: UploadFile = File(..., description="Post-change T2 image"),
    threshold: float = Form(0.5)
):
    """Direct file upload endpoint for testing or client upload."""
    if not engine:
        raise HTTPException(status_code=503, detail="ChangeStar Engine is not initialized")

    uploads_dir = BASE_DIR / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    t1_save = uploads_dir / f"upload_t1_{int(time.time() * 1000)}_{file_t1.filename}"
    t2_save = uploads_dir / f"upload_t2_{int(time.time() * 1000)}_{file_t2.filename}"

    with open(t1_save, "wb") as f:
        f.write(await file_t1.read())
    with open(t2_save, "wb") as f:
        f.write(await file_t2.read())

    return predict(ChangeStarRequest(t1_path=str(t1_save), t2_path=str(t2_save), threshold=threshold))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("model_services.changestar_server:app", host="127.0.0.1", port=8001, reload=False)
