# backend/config/settings.py
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "SatQuery AI Backend"
    API_V1_STR: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Model Execution Timeout
    MODEL_TIMEOUT: int = 180

    # Test & Offline Fallback: When False, live inference never falls back to mock adapters
    # and strictly reports unavailability or errors
    ENABLE_MOCK_FALLBACK_FOR_TESTS: bool = False

    # Specialist Model 1: GeoChat-7B (Single Image VQA, Captioning, Grounding)
    GEOCHAT_API_URL: Optional[str] = None
    GEOCHAT_API_TYPE: str = "gradio"  # 'gradio', 'rest', 'local', 'mock'
    GEOCHAT_API_ENDPOINT: str = "predict"

    # Specialist Model 2: ChangeStar (Bi-temporal Change Detection & Change VQA)
    CHANGE_MODEL_API_URL: Optional[str] = None
    CHANGE_MODEL_API_TYPE: str = "gradio"
    CHANGE_MODEL_API_ENDPOINT: str = "predict"

    # Specialist Model 3: CROMA (Optical + SAR Multimodal Cross-Attention)
    CROMA_API_URL: Optional[str] = None
    CROMA_API_TYPE: str = "gradio"
    CROMA_API_ENDPOINT: str = "predict"

    # Specialist Model 4: Visual Grounding Specialist
    GROUNDING_API_URL: Optional[str] = None
    GROUNDING_API_TYPE: str = "gradio"
    GROUNDING_API_ENDPOINT: str = "predict"

    # Storage & Persistence
    DATABASE_URL: str = "sqlite:///./satquery.db"
    EXPERIMENT_LOGGING: bool = True
    CACHE_ENABLED: bool = False

    # Directories
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    REPORTS_DIR: str = str(BASE_DIR / "generated_reports")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
