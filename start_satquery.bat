@echo off
title SatQuery AI - Full Platform Launcher
echo ========================================================
echo          Starting SatQuery AI Platform
echo ========================================================
echo.

echo [1/4] Starting ChangeStar Microservice on port 8001...
start "SatQuery - ChangeStar (Port 8001)" cmd /k "set PYTHONPATH=%CD%&& python -m uvicorn model_services.changestar_server:app --host 127.0.0.1 --port 8001"

echo [2/4] Starting CROMA Microservice on port 8002...
start "SatQuery - CROMA (Port 8002)" cmd /k "set PYTHONPATH=%CD%&& python -m uvicorn model_services.croma_server:app --host 127.0.0.1 --port 8002"

echo [3/4] Starting SatQuery Backend Gateway on port 8000...
start "SatQuery - Backend Gateway (Port 8000)" cmd /k "set PYTHONPATH=%CD%&& python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

echo [4/4] Starting React Frontend on port 3000...
start "SatQuery - Frontend UI (Port 3000)" cmd /k "cd frontend && npm run dev -- --host 127.0.0.1"

echo.
echo All services have been launched in separate windows!
echo - Frontend UI:      http://127.0.0.1:3000
echo - Backend API Docs: http://127.0.0.1:8000/docs
echo - ChangeStar API:   http://127.0.0.1:8001/health
echo - CROMA API:        http://127.0.0.1:8002/health
echo.
pause
