# backend/main.py
import os
import sys
from pathlib import Path

# Ensure SAT root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging

from backend.config.settings import settings
from backend.config.endpoint_config import CentralConfigManager
from backend.database.database import init_db
from backend.api.routes import api_router

logger = logging.getLogger("SatQueryAI")

# Initialize SQLite database schema
init_db()

app = FastAPI(
    title="SatQuery AI",
    description="An Agentic Vision-Language Framework for Query-Driven Multimodal Remote-Sensing Analysis",
    version="1.0.0"
)

@app.on_event("startup")
def startup_validation():
    config = CentralConfigManager.get_config()
    messages = config.validate_configuration()
    print("\n--- SatQuery AI Model Endpoints Startup Validation ---")
    for msg in messages:
        print(f"  [Endpoint Validation] {msg}")
    print("-----------------------------------------------------\n")

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for preview and overlay retrieval
app.mount("/api/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include master API router at /api and root for maximum flexibility
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router)

@app.get("/")
def read_root():
    return {
        "message": "SatQuery AI Research API is running",
        "docs_url": "/docs",
        "health_url": f"{settings.API_V1_STR}/health",
        "status_url": f"{settings.API_V1_STR}/system-status"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
