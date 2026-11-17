# backend/api/routes.py
from fastapi import APIRouter
from backend.api.health import router as health_router
from backend.api.models import router as models_router
from backend.api.analysis import router as analysis_router
from backend.api.reports import router as reports_router
from backend.api.experiments import router as experiments_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(models_router)
api_router.include_router(analysis_router)
api_router.include_router(reports_router)
api_router.include_router(experiments_router)
