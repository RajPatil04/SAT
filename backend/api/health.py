# backend/api/health.py
from fastapi import APIRouter
from backend.config.settings import settings
from backend.router.schemas import SystemStatusResponse, ModelStatus
from backend.router.model_registry import ModelRegistry
from backend.database.database import SessionLocal
from backend.database.models import ExperimentRecordDB

router = APIRouter(tags=["System Health"])

@router.get("/health")
async def get_health():
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0"
    }

@router.get("/system-status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    Returns comprehensive system operational status for all components.
    Carefully distinguishes between ONLINE, OFFLINE, NOT CONFIGURED, and MOCK.
    """
    # 1. Database status & experiment count
    db_status = "ONLINE"
    exp_count = 0
    try:
        db = SessionLocal()
        exp_count = db.query(ExperimentRecordDB).count()
        db.close()
    except Exception:
        db_status = "ERROR"

    # 2. Model statuses
    model_statuses = {}
    for m in ModelRegistry.list_models():
        model_statuses[m.display_name] = m.status.value

    return SystemStatusResponse(
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        status="OPERATIONAL",
        fastapi="ONLINE",
        router="ONLINE",
        models=model_statuses,
        database=db_status,
        experiment_logger="ONLINE" if settings.EXPERIMENT_LOGGING else "DISABLED",
        active_experiments_count=exp_count
    )
